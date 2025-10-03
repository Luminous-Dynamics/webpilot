#!/usr/bin/env python3
"""
Visual Regression Testing - Automated screenshot comparison
Detects pixel-perfect differences in web pages
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageChops
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL not available. Install with: pip install pillow")


class VisualRegression:
    """Visual regression testing with screenshot comparison"""
    
    def __init__(self, baseline_dir: str = "visual_baselines", diff_dir: str = "visual_diffs"):
        """
        Initialize visual regression tester.
        
        Args:
            baseline_dir: Directory for baseline screenshots
            diff_dir: Directory for diff images
        """
        self.baseline_dir = Path(baseline_dir)
        self.diff_dir = Path(diff_dir)
        self.baseline_dir.mkdir(exist_ok=True)
        self.diff_dir.mkdir(exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.baseline_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load baseline metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save baseline metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def take_baseline(self, name: str, page, full_page: bool = True) -> str:
        """
        Take baseline screenshot for future comparisons.
        
        Args:
            name: Name for this baseline (e.g., "homepage", "login-page")
            page: Playwright page object
            full_page: Take full page screenshot
            
        Returns:
            Path to baseline screenshot
        """
        # Generate filename
        filename = f"{name}_baseline.png"
        filepath = self.baseline_dir / filename
        
        # Take screenshot
        page.screenshot(path=str(filepath), full_page=full_page)
        
        # Save metadata
        self.metadata[name] = {
            'filename': filename,
            'created_at': datetime.now().isoformat(),
            'full_page': full_page,
            'url': page.url,
            'viewport': page.viewport_size
        }
        self._save_metadata()
        
        print(f"✅ Baseline saved: {filepath}")
        return str(filepath)
    
    def compare_with_baseline(
        self,
        name: str,
        page,
        threshold: float = 0.1,
        full_page: bool = True
    ) -> Dict:
        """
        Compare current page with baseline.
        
        Args:
            name: Name of baseline to compare with
            page: Playwright page object
            threshold: Acceptable difference threshold (%)
            full_page: Take full page screenshot
            
        Returns:
            Comparison results
        """
        if not PIL_AVAILABLE:
            return {
                'success': False,
                'error': 'PIL not available. Install with: pip install pillow'
            }
        
        # Check if baseline exists
        if name not in self.metadata:
            return {
                'success': False,
                'error': f'No baseline found for "{name}". Create one with take_baseline()'
            }
        
        # Take current screenshot
        current_filename = f"{name}_current.png"
        current_path = self.diff_dir / current_filename
        page.screenshot(path=str(current_path), full_page=full_page)
        
        # Load images
        baseline_path = self.baseline_dir / self.metadata[name]['filename']
        baseline_img = Image.open(baseline_path)
        current_img = Image.open(current_path)
        
        # Compare
        result = self._compare_images(baseline_img, current_img, name, threshold)
        
        # Print result
        if result['match']:
            print(f"✅ Visual match (diff: {result['difference_pct']:.2f}%)")
        else:
            print(f"❌ Visual difference detected ({result['difference_pct']:.2f}%)")
            print(f"   Diff image: {result['diff_path']}")
        
        return result
    
    def _compare_images(
        self,
        baseline: Image.Image,
        current: Image.Image,
        name: str,
        threshold: float
    ) -> Dict:
        """
        Compare two images pixel by pixel.
        
        Returns:
            Comparison results with difference percentage
        """
        # Ensure images are same size
        if baseline.size != current.size:
            # Resize current to match baseline
            current = current.resize(baseline.size, Image.LANCZOS)
        
        # Convert to RGB
        baseline_rgb = baseline.convert('RGB')
        current_rgb = current.convert('RGB')
        
        # Calculate difference
        diff = ImageChops.difference(baseline_rgb, current_rgb)
        
        # Get difference statistics
        diff_pixels = 0
        total_pixels = baseline.width * baseline.height * 3  # RGB channels
        
        # Count different pixels
        for pixel in diff.getdata():
            if pixel != (0, 0, 0):
                diff_pixels += sum(pixel)
        
        # Calculate percentage
        difference_pct = (diff_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Create visual diff image
        diff_path = None
        if difference_pct > 0:
            diff_path = self._create_diff_image(baseline_rgb, current_rgb, diff, name)
        
        return {
            'success': True,
            'match': difference_pct <= threshold,
            'difference_pct': difference_pct,
            'threshold': threshold,
            'diff_pixels': diff_pixels,
            'total_pixels': total_pixels,
            'diff_path': diff_path,
            'baseline_size': baseline.size,
            'current_size': current.size
        }
    
    def _create_diff_image(
        self,
        baseline: Image.Image,
        current: Image.Image,
        diff: Image.Image,
        name: str
    ) -> str:
        """
        Create visual diff image showing differences.
        
        Returns:
            Path to diff image
        """
        # Create side-by-side comparison
        width = baseline.width * 3  # baseline + current + diff
        height = baseline.height
        
        comparison = Image.new('RGB', (width, height))
        
        # Paste images
        comparison.paste(baseline, (0, 0))
        comparison.paste(current, (baseline.width, 0))
        
        # Highlight differences in red
        diff_highlighted = diff.copy()
        diff_data = list(diff_highlighted.getdata())
        
        # Make differences more visible (red highlights)
        highlighted_data = []
        for pixel in diff_data:
            if pixel != (0, 0, 0):
                # Amplify differences in red
                highlighted_data.append((255, pixel[1], pixel[2]))
            else:
                highlighted_data.append((0, 0, 0))
        
        diff_highlighted.putdata(highlighted_data)
        comparison.paste(diff_highlighted, (baseline.width * 2, 0))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        labels = ["BASELINE", "CURRENT", "DIFF"]
        for i, label in enumerate(labels):
            x = i * baseline.width + 10
            draw.text((x, 10), label, fill=(255, 255, 0))
        
        # Save
        diff_filename = f"{name}_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        diff_path = self.diff_dir / diff_filename
        comparison.save(diff_path)
        
        return str(diff_path)
    
    def approve_changes(self, name: str):
        """
        Approve current screenshot as new baseline.
        Replaces old baseline with current screenshot.
        
        Args:
            name: Name of baseline to update
        """
        if name not in self.metadata:
            print(f"❌ No baseline found for '{name}'")
            return
        
        # Move current to baseline
        current_path = self.diff_dir / f"{name}_current.png"
        if not current_path.exists():
            print(f"❌ No current screenshot found. Run compare_with_baseline() first")
            return
        
        baseline_path = self.baseline_dir / self.metadata[name]['filename']
        
        # Replace baseline
        current_img = Image.open(current_path)
        current_img.save(baseline_path)
        
        # Update metadata
        self.metadata[name]['updated_at'] = datetime.now().isoformat()
        self._save_metadata()
        
        print(f"✅ Baseline updated for '{name}'")
    
    def list_baselines(self) -> List[Dict]:
        """List all saved baselines"""
        return [
            {
                'name': name,
                **info
            }
            for name, info in self.metadata.items()
        ]
    
    def delete_baseline(self, name: str):
        """Delete a baseline"""
        if name in self.metadata:
            # Delete file
            baseline_path = self.baseline_dir / self.metadata[name]['filename']
            if baseline_path.exists():
                baseline_path.unlink()
            
            # Remove from metadata
            del self.metadata[name]
            self._save_metadata()
            
            print(f"✅ Baseline '{name}' deleted")
        else:
            print(f"❌ No baseline found for '{name}'")
    
    def test_page(self, name: str, page, threshold: float = 0.1) -> bool:
        """
        Test page against baseline (convenience method).
        
        Returns:
            True if match, False if difference detected
        """
        result = self.compare_with_baseline(name, page, threshold)
        return result.get('match', False)


# Quick usage functions
def compare_pages(name: str, page, threshold: float = 0.1) -> bool:
    """Quick comparison function"""
    vr = VisualRegression()
    
    # Check if baseline exists, create if not
    baselines = vr.list_baselines()
    baseline_names = [b['name'] for b in baselines]
    
    if name not in baseline_names:
        print(f"📸 Creating baseline for '{name}'...")
        vr.take_baseline(name, page)
        return True
    else:
        result = vr.compare_with_baseline(name, page, threshold)
        return result.get('match', False)


# Example usage
if __name__ == "__main__":
    print("🎨 Visual Regression Testing Demo\n")
    print("This module provides automated screenshot comparison.")
    print("\nUsage:")
    print("  vr = VisualRegression()")
    print("  vr.take_baseline('homepage', page)")
    print("  result = vr.compare_with_baseline('homepage', page)")
    print("  if result['match']:")
    print("      print('✅ No visual changes')")
    print("  else:")
    print("      print(f'❌ {result['difference_pct']:.2f}% difference')")
