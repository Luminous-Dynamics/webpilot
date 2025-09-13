#!/usr/bin/env python3
"""
WebPilot Vision - Visual element detection and OCR capabilities
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import base64
import io

# Try importing vision libraries
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL not available. Install with: pip install pillow")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  Tesseract not available. Install with: pip install pytesseract")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️  OpenCV not available. Install with: pip install opencv-python")


class WebPilotVision:
    """Visual element detection for WebPilot"""
    
    def __init__(self):
        """Initialize vision capabilities"""
        self.logger = logging.getLogger('WebPilotVision')
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check which vision libraries are available"""
        deps = {
            'PIL': PIL_AVAILABLE,
            'Tesseract': TESSERACT_AVAILABLE,
            'OpenCV': OPENCV_AVAILABLE
        }
        
        available = [k for k, v in deps.items() if v]
        missing = [k for k, v in deps.items() if not v]
        
        if available:
            self.logger.info(f"Vision libraries available: {', '.join(available)}")
        if missing:
            self.logger.warning(f"Vision libraries missing: {', '.join(missing)}")
        
        return deps
    
    def extract_text_from_image(self, image_path: str) -> Dict:
        """Extract text from image using OCR"""
        
        if not TESSERACT_AVAILABLE:
            return {
                'success': False,
                'error': 'Tesseract not available. Install with: pip install pytesseract'
            }
        
        try:
            # Open image
            if PIL_AVAILABLE:
                image = Image.open(image_path)
            else:
                # Fallback to reading raw
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                return {
                    'success': False,
                    'error': 'PIL required for OCR'
                }
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Get detailed data with bounding boxes
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract words with positions
            words = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    words.append({
                        'text': data['text'][i],
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            
            return {
                'success': True,
                'full_text': text,
                'words': words,
                'word_count': len(words)
            }
            
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_text_in_image(self, image_path: str, search_text: str) -> Dict:
        """Find specific text in image and return its location"""
        
        ocr_result = self.extract_text_from_image(image_path)
        
        if not ocr_result['success']:
            return ocr_result
        
        found_elements = []
        search_lower = search_text.lower()
        
        for word in ocr_result.get('words', []):
            if search_lower in word['text'].lower():
                found_elements.append({
                    'text': word['text'],
                    'x': word['x'],
                    'y': word['y'],
                    'center_x': word['x'] + word['width'] // 2,
                    'center_y': word['y'] + word['height'] // 2,
                    'width': word['width'],
                    'height': word['height'],
                    'confidence': word['confidence']
                })
        
        return {
            'success': True,
            'search_text': search_text,
            'found': len(found_elements) > 0,
            'elements': found_elements,
            'count': len(found_elements)
        }
    
    def detect_buttons(self, image_path: str) -> Dict:
        """Detect button-like elements in image"""
        
        if not OPENCV_AVAILABLE:
            return {
                'success': False,
                'error': 'OpenCV not available. Install with: pip install opencv-python'
            }
        
        try:
            # Read image
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Find contours (potential buttons)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            buttons = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for button-like shapes
                aspect_ratio = w / h if h > 0 else 0
                area = w * h
                
                # Typical button characteristics
                if (0.5 < aspect_ratio < 5.0 and  # Not too tall or wide
                    100 < area < 50000 and  # Reasonable size
                    w > 30 and h > 15):  # Minimum dimensions
                    
                    buttons.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'center_x': int(x + w // 2),
                        'center_y': int(y + h // 2),
                        'area': int(area),
                        'aspect_ratio': round(aspect_ratio, 2)
                    })
            
            # Sort by y-position (top to bottom)
            buttons.sort(key=lambda b: b['y'])
            
            return {
                'success': True,
                'buttons': buttons,
                'count': len(buttons)
            }
            
        except Exception as e:
            self.logger.error(f"Button detection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_input_fields(self, image_path: str) -> Dict:
        """Detect input field-like elements"""
        
        if not OPENCV_AVAILABLE:
            return {
                'success': False,
                'error': 'OpenCV not available'
            }
        
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Look for horizontal lines (typical of input fields)
            edges = cv2.Canny(gray, 30, 100)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
            
            input_fields = []
            if lines is not None:
                # Group horizontal lines that might be input fields
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Check if line is mostly horizontal
                    if abs(y2 - y1) < 10 and abs(x2 - x1) > 50:
                        input_fields.append({
                            'x': min(x1, x2),
                            'y': min(y1, y2) - 20,  # Assume field is above line
                            'width': abs(x2 - x1),
                            'height': 30,  # Estimated height
                            'center_x': (x1 + x2) // 2,
                            'center_y': (y1 + y2) // 2 - 10
                        })
            
            return {
                'success': True,
                'input_fields': input_fields,
                'count': len(input_fields)
            }
            
        except Exception as e:
            self.logger.error(f"Input field detection failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def highlight_elements(self, image_path: str, elements: List[Dict], 
                          output_path: Optional[str] = None) -> Dict:
        """Draw boxes around detected elements"""
        
        if not PIL_AVAILABLE:
            return {
                'success': False,
                'error': 'PIL not available'
            }
        
        try:
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Draw rectangles around elements
            for elem in elements:
                x = elem.get('x', 0)
                y = elem.get('y', 0)
                w = elem.get('width', 0)
                h = elem.get('height', 0)
                
                # Draw rectangle
                draw.rectangle(
                    [(x, y), (x + w, y + h)],
                    outline='red',
                    width=2
                )
                
                # Add text label if available
                if 'text' in elem:
                    draw.text((x, y - 15), elem['text'], fill='red')
            
            # Save highlighted image
            if not output_path:
                output_path = image_path.replace('.png', '_highlighted.png')
            
            image.save(output_path)
            
            return {
                'success': True,
                'output_path': output_path,
                'elements_highlighted': len(elements)
            }
            
        except Exception as e:
            self.logger.error(f"Highlighting failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_clickable_at_text(self, image_path: str, text: str) -> Dict:
        """Find clickable coordinates for text"""
        
        result = self.find_text_in_image(image_path, text)
        
        if not result['success'] or not result['found']:
            return result
        
        # Return the first match's center coordinates
        first_match = result['elements'][0]
        
        return {
            'success': True,
            'text': text,
            'found': True,
            'click_x': first_match['center_x'],
            'click_y': first_match['center_y'],
            'confidence': first_match.get('confidence', 0)
        }
    
    def analyze_screenshot(self, image_path: str) -> Dict:
        """Comprehensive analysis of screenshot"""
        
        analysis = {
            'image_path': image_path,
            'timestamp': time.time()
        }
        
        # Extract text
        ocr_result = self.extract_text_from_image(image_path)
        if ocr_result['success']:
            analysis['text'] = {
                'full_text': ocr_result['full_text'],
                'word_count': ocr_result['word_count']
            }
        
        # Detect buttons
        button_result = self.detect_buttons(image_path)
        if button_result['success']:
            analysis['buttons'] = {
                'count': button_result['count'],
                'locations': button_result['buttons'][:5]  # Top 5
            }
        
        # Detect input fields
        input_result = self.detect_input_fields(image_path)
        if input_result['success']:
            analysis['input_fields'] = {
                'count': input_result['count'],
                'locations': input_result['input_fields'][:5]
            }
        
        return analysis


def test_vision_capabilities():
    """Test vision capabilities"""
    
    print("🔍 Testing WebPilot Vision Capabilities")
    print("=" * 50)
    
    vision = WebPilotVision()
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    deps = vision.check_dependencies()
    for lib, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {lib}: {status}")
    
    # Create a test image if PIL is available
    if PIL_AVAILABLE:
        print("\n2. Creating test image...")
        
        # Create simple test image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some text
        draw.text((50, 30), "Click Here", fill='black')
        draw.text((50, 80), "Username:", fill='black')
        draw.text((50, 120), "Submit", fill='black')
        
        # Add rectangles (simulating buttons)
        draw.rectangle([(40, 25), (120, 50)], outline='black', width=1)
        draw.rectangle([(40, 115), (100, 140)], outline='black', width=1)
        
        # Save test image
        test_path = '/tmp/webpilot_vision_test.png'
        img.save(test_path)
        print(f"   Test image saved: {test_path}")
        
        # Test OCR
        print("\n3. Testing OCR...")
        ocr_result = vision.extract_text_from_image(test_path)
        if ocr_result['success']:
            print(f"   ✅ Text extracted: {ocr_result.get('word_count', 0)} words")
        else:
            print(f"   ❌ OCR failed: {ocr_result['error']}")
        
        # Test text finding
        print("\n4. Testing text search...")
        find_result = vision.find_text_in_image(test_path, "Click")
        if find_result['success'] and find_result['found']:
            print(f"   ✅ Found 'Click' at: ({find_result['elements'][0]['center_x']}, {find_result['elements'][0]['center_y']})")
        else:
            print("   ❌ Text not found")
    
    print("\n✨ Vision capabilities test complete!")
    print("\nCapabilities available:")
    print("  • OCR text extraction")
    print("  • Text location finding")
    print("  • Button detection")
    print("  • Input field detection")
    print("  • Element highlighting")
    print("  • Click coordinate finding")


if __name__ == "__main__":
    test_vision_capabilities()