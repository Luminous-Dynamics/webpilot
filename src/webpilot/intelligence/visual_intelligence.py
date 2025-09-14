"""
Visual Intelligence for WebPilot

Enables LLMs to understand and interact with web pages through visual analysis.
"""

import base64
import io
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np

from ..core import WebPilot, ActionResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VisualElement:
    """Represents a visual element on the page."""
    type: str  # button, link, input, text, image, etc.
    text: Optional[str]
    location: Tuple[int, int]  # x, y coordinates
    size: Tuple[int, int]  # width, height
    confidence: float
    attributes: Dict[str, Any]


@dataclass  
class VisualAnalysis:
    """Results of visual page analysis."""
    elements: List[VisualElement]
    layout: str  # Description of page layout
    primary_content: str  # Main content area
    navigation: List[str]  # Navigation elements
    forms: List[Dict[str, Any]]  # Form structures
    images: List[Dict[str, Any]]  # Image descriptions
    overall_description: str


class VisualIntelligence:
    """
    Visual intelligence system for WebPilot.
    
    Enables LLMs to understand web pages visually and interact
    based on visual descriptions rather than selectors.
    """
    
    def __init__(self, pilot: Optional[WebPilot] = None):
        """
        Initialize visual intelligence.
        
        Args:
            pilot: WebPilot instance to use
        """
        self.pilot = pilot or WebPilot()
        self.logger = get_logger(__name__)
        self.current_screenshot = None
        self.current_analysis = None
        
    def capture_and_analyze(self) -> VisualAnalysis:
        """
        Capture screenshot and analyze the page visually.
        
        Returns:
            Visual analysis of the current page
        """
        # Take screenshot
        screenshot_result = self.pilot.screenshot()
        if not screenshot_result.success:
            raise RuntimeError(f"Failed to capture screenshot: {screenshot_result.error}")
            
        screenshot_path = screenshot_result.data
        self.current_screenshot = screenshot_path
        
        # Load image
        image = Image.open(screenshot_path)
        
        # Perform visual analysis
        analysis = self._analyze_image(image)
        self.current_analysis = analysis
        
        return analysis
        
    def _analyze_image(self, image: Image.Image) -> VisualAnalysis:
        """
        Analyze an image to extract visual elements.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Visual analysis results
        """
        # This is a simplified implementation
        # In production, you'd use computer vision models
        
        elements = []
        
        # Try to detect elements using OCR if available
        try:
            import pytesseract
            
            # Get OCR data
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text elements
            for i in range(len(ocr_data['text'])):
                if ocr_data['text'][i].strip():
                    element = VisualElement(
                        type='text',
                        text=ocr_data['text'][i],
                        location=(ocr_data['left'][i], ocr_data['top'][i]),
                        size=(ocr_data['width'][i], ocr_data['height'][i]),
                        confidence=ocr_data['conf'][i] / 100.0,
                        attributes={}
                    )
                    elements.append(element)
                    
        except ImportError:
            logger.warning("pytesseract not available, using basic analysis")
            
        # Try to detect UI elements using template matching or ML
        elements.extend(self._detect_ui_elements(image))
        
        # Analyze layout
        layout = self._analyze_layout(image, elements)
        
        # Extract forms
        forms = self._detect_forms(elements)
        
        # Extract navigation
        navigation = self._detect_navigation(elements)
        
        # Generate description
        description = self._generate_description(elements, layout)
        
        return VisualAnalysis(
            elements=elements,
            layout=layout,
            primary_content=self._identify_primary_content(elements),
            navigation=navigation,
            forms=forms,
            images=self._detect_images(image),
            overall_description=description
        )
        
    def _detect_ui_elements(self, image: Image.Image) -> List[VisualElement]:
        """Detect UI elements like buttons, inputs, links."""
        elements = []
        
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Simple edge detection to find rectangles (buttons, inputs)
        try:
            import cv2
            
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (likely UI elements)
                if 50 < w < 500 and 20 < h < 100:
                    # Classify element type based on aspect ratio and position
                    if w / h > 3:
                        elem_type = 'input'
                    elif 1.5 < w / h < 3:
                        elem_type = 'button'
                    else:
                        elem_type = 'element'
                        
                    elements.append(VisualElement(
                        type=elem_type,
                        text=None,
                        location=(x, y),
                        size=(w, h),
                        confidence=0.7,
                        attributes={'detected_by': 'edge_detection'}
                    ))
                    
        except ImportError:
            logger.warning("OpenCV not available for advanced element detection")
            
        return elements
        
    def _analyze_layout(self, image: Image.Image, elements: List[VisualElement]) -> str:
        """Analyze page layout structure."""
        width, height = image.size
        
        # Simple layout detection based on element positions
        top_elements = [e for e in elements if e.location[1] < height * 0.2]
        middle_elements = [e for e in elements if height * 0.2 <= e.location[1] < height * 0.8]
        bottom_elements = [e for e in elements if e.location[1] >= height * 0.8]
        
        layout_parts = []
        
        if top_elements:
            layout_parts.append("header at top")
        if middle_elements:
            layout_parts.append("main content in center")
        if bottom_elements:
            layout_parts.append("footer at bottom")
            
        # Check for sidebars
        left_elements = [e for e in middle_elements if e.location[0] < width * 0.25]
        right_elements = [e for e in middle_elements if e.location[0] > width * 0.75]
        
        if left_elements:
            layout_parts.append("left sidebar")
        if right_elements:
            layout_parts.append("right sidebar")
            
        return f"Page layout: {', '.join(layout_parts) if layout_parts else 'single column'}"
        
    def _detect_forms(self, elements: List[VisualElement]) -> List[Dict[str, Any]]:
        """Detect form structures on the page."""
        forms = []
        
        # Group nearby input elements as forms
        input_elements = [e for e in elements if e.type in ['input', 'button']]
        
        if input_elements:
            # Simple clustering by proximity
            current_form = {
                'fields': [],
                'buttons': [],
                'location': None
            }
            
            for elem in input_elements:
                if elem.type == 'input':
                    current_form['fields'].append({
                        'location': elem.location,
                        'size': elem.size,
                        'text': elem.text
                    })
                elif elem.type == 'button':
                    current_form['buttons'].append({
                        'location': elem.location,
                        'text': elem.text or 'Submit'
                    })
                    
            if current_form['fields'] or current_form['buttons']:
                forms.append(current_form)
                
        return forms
        
    def _detect_navigation(self, elements: List[VisualElement]) -> List[str]:
        """Detect navigation elements."""
        nav_items = []
        
        # Look for text elements that might be navigation
        for elem in elements:
            if elem.text and elem.type == 'text':
                text_lower = elem.text.lower()
                # Common navigation words
                if any(word in text_lower for word in ['home', 'about', 'contact', 'menu', 'products', 'services']):
                    nav_items.append(elem.text)
                    
        return nav_items
        
    def _identify_primary_content(self, elements: List[VisualElement]) -> str:
        """Identify the primary content area."""
        # Find the largest text block
        text_elements = [e for e in elements if e.type == 'text' and e.text]
        
        if text_elements:
            # Sort by size (area)
            text_elements.sort(key=lambda e: e.size[0] * e.size[1], reverse=True)
            
            # Combine top text elements
            primary_texts = [e.text for e in text_elements[:5]]
            return ' '.join(primary_texts)
            
        return "No primary content detected"
        
    def _detect_images(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect images on the page."""
        # This would use more sophisticated image detection in production
        return [
            {
                'description': 'Page contains images',
                'count': 'multiple'
            }
        ]
        
    def _generate_description(self, elements: List[VisualElement], layout: str) -> str:
        """Generate overall page description."""
        descriptions = [layout]
        
        # Count element types
        type_counts = {}
        for elem in elements:
            type_counts[elem.type] = type_counts.get(elem.type, 0) + 1
            
        for elem_type, count in type_counts.items():
            descriptions.append(f"{count} {elem_type} elements")
            
        return f"Web page with {'. '.join(descriptions)}."
        
    def click_by_description(self, description: str) -> ActionResult:
        """
        Click an element based on visual description.
        
        Args:
            description: Natural language description of what to click
            
        Returns:
            Click result
        """
        if not self.current_analysis:
            self.capture_and_analyze()
            
        # Find matching element
        element = self._find_element_by_description(description)
        
        if element:
            # Click at element center
            x = element.location[0] + element.size[0] // 2
            y = element.location[1] + element.size[1] // 2
            
            return self.pilot.click(x=x, y=y)
        else:
            return ActionResult(
                success=False,
                error=f"Could not find element matching: {description}"
            )
            
    def _find_element_by_description(self, description: str) -> Optional[VisualElement]:
        """Find element matching description."""
        if not self.current_analysis:
            return None
            
        description_lower = description.lower()
        
        # Search through elements
        for element in self.current_analysis.elements:
            if element.text:
                if element.text.lower() in description_lower or description_lower in element.text.lower():
                    return element
                    
            # Check element type
            if element.type in description_lower:
                return element
                
        return None
        
    def type_at_description(self, description: str, text: str) -> ActionResult:
        """
        Type text at element matching description.
        
        Args:
            description: Description of input field
            text: Text to type
            
        Returns:
            Type result
        """
        if not self.current_analysis:
            self.capture_and_analyze()
            
        element = self._find_element_by_description(description)
        
        if element:
            # Click to focus
            x = element.location[0] + element.size[0] // 2
            y = element.location[1] + element.size[1] // 2
            
            click_result = self.pilot.click(x=x, y=y)
            if click_result.success:
                return self.pilot.type_text(text)
            else:
                return click_result
        else:
            return ActionResult(
                success=False,
                error=f"Could not find input matching: {description}"
            )
            
    def describe_page(self) -> str:
        """
        Generate natural language description of current page.
        
        Returns:
            Page description
        """
        if not self.current_analysis:
            self.capture_and_analyze()
            
        analysis = self.current_analysis
        
        description_parts = [
            analysis.overall_description,
            f"The page has {len(analysis.navigation)} navigation items.",
            f"There are {len(analysis.forms)} forms on the page.",
        ]
        
        if analysis.primary_content:
            description_parts.append(f"Primary content: {analysis.primary_content[:200]}...")
            
        return "\n".join(description_parts)
        
    def suggest_actions(self) -> List[str]:
        """
        Suggest possible actions based on page content.
        
        Returns:
            List of suggested actions
        """
        if not self.current_analysis:
            self.capture_and_analyze()
            
        suggestions = []
        
        # Suggest based on detected elements
        for form in self.current_analysis.forms:
            if form['buttons']:
                suggestions.append("Fill and submit the form")
                
        if self.current_analysis.navigation:
            suggestions.append(f"Navigate to: {', '.join(self.current_analysis.navigation[:3])}")
            
        # Suggest based on element types
        element_types = set(e.type for e in self.current_analysis.elements)
        
        if 'button' in element_types:
            suggestions.append("Click on buttons to interact")
        if 'input' in element_types:
            suggestions.append("Enter text in input fields")
            
        return suggestions
        
    def export_for_llm(self) -> Dict[str, Any]:
        """
        Export visual analysis in format suitable for LLM consumption.
        
        Returns:
            Structured data for LLM
        """
        if not self.current_analysis:
            self.capture_and_analyze()
            
        analysis = self.current_analysis
        
        return {
            'description': analysis.overall_description,
            'layout': analysis.layout,
            'primary_content': analysis.primary_content[:500],
            'navigation': analysis.navigation,
            'forms': [
                {
                    'field_count': len(form['fields']),
                    'has_submit': len(form['buttons']) > 0
                }
                for form in analysis.forms
            ],
            'clickable_elements': [
                {
                    'text': e.text,
                    'type': e.type,
                    'position': f"x={e.location[0]}, y={e.location[1]}"
                }
                for e in analysis.elements
                if e.type in ['button', 'link'] and e.text
            ][:10],  # Limit to 10 for brevity
            'suggested_actions': self.suggest_actions()
        }
        
    def screenshot_to_base64(self) -> str:
        """
        Convert current screenshot to base64 for LLM vision models.
        
        Returns:
            Base64 encoded image
        """
        if not self.current_screenshot:
            self.capture_and_analyze()
            
        with open(self.current_screenshot, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')


class VisualWebPilot(WebPilot):
    """
    WebPilot with visual intelligence capabilities.
    
    Extends WebPilot to enable visual understanding and interaction.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize VisualWebPilot."""
        super().__init__(*args, **kwargs)
        self.visual = VisualIntelligence(self)
        
    def visual_click(self, description: str) -> ActionResult:
        """Click element by visual description."""
        return self.visual.click_by_description(description)
        
    def visual_type(self, description: str, text: str) -> ActionResult:
        """Type in element by visual description."""
        return self.visual.type_at_description(description, text)
        
    def describe_current_page(self) -> str:
        """Get natural language description of current page."""
        return self.visual.describe_page()
        
    def get_visual_analysis(self) -> Dict[str, Any]:
        """Get structured visual analysis for LLM."""
        return self.visual.export_for_llm()
        
    def suggest_next_actions(self) -> List[str]:
        """Get suggested actions for current page."""
        return self.visual.suggest_actions()
        
    def capture_for_vision_llm(self) -> str:
        """Capture screenshot as base64 for vision LLMs."""
        return self.visual.screenshot_to_base64()


# Integration with LLMs

def create_visual_llm_prompt(visual_analysis: Dict[str, Any], task: str) -> str:
    """
    Create prompt for LLM with visual context.
    
    Args:
        visual_analysis: Visual analysis from VisualIntelligence
        task: Task to accomplish
        
    Returns:
        Formatted prompt for LLM
    """
    prompt = f"""
You are controlling a web browser to accomplish this task: {task}

Current page analysis:
- Description: {visual_analysis['description']}
- Layout: {visual_analysis['layout']}
- Navigation options: {', '.join(visual_analysis['navigation'])}
- Forms: {len(visual_analysis.get('forms', []))} forms detected
- Suggested actions: {', '.join(visual_analysis['suggested_actions'])}

Available clickable elements:
"""
    
    for elem in visual_analysis.get('clickable_elements', [])[:5]:
        prompt += f"- {elem['type']}: '{elem['text']}' at {elem['position']}\n"
        
    prompt += f"""
Based on this analysis, what specific action should we take to accomplish: {task}?

Respond with one of these commands:
- click "[element text or description]"
- type "[text to type]" in "[field description]"  
- navigate to "[navigation item]"
- screenshot
- extract content
"""
    
    return prompt


# Example usage with vision LLMs

class VisionLLMWebPilot:
    """
    WebPilot integration with vision-capable LLMs.
    
    For LLMs that can directly process images (GPT-4V, Claude, etc.)
    """
    
    def __init__(self, pilot: Optional[VisualWebPilot] = None):
        """Initialize vision LLM integration."""
        self.pilot = pilot or VisualWebPilot()
        
    async def execute_with_vision_llm(self, task: str, llm_client) -> ActionResult:
        """
        Execute task using vision LLM.
        
        Args:
            task: Task to accomplish
            llm_client: LLM client that supports vision
            
        Returns:
            Execution result
        """
        # Capture screenshot
        screenshot_base64 = self.pilot.capture_for_vision_llm()
        
        # Send to vision LLM
        response = await llm_client.analyze_image(
            image=screenshot_base64,
            prompt=f"Help me accomplish this task: {task}\nWhat should I click or type?"
        )
        
        # Parse and execute response
        return self._execute_llm_response(response)
        
    def _execute_llm_response(self, response: str) -> ActionResult:
        """Parse and execute LLM response."""
        response_lower = response.lower()
        
        if "click" in response_lower:
            # Extract what to click
            import re
            match = re.search(r'click[^\'"]*["\']([^"\']+)["\']', response, re.IGNORECASE)
            if match:
                return self.pilot.visual_click(match.group(1))
                
        elif "type" in response_lower:
            # Extract what to type
            import re
            type_match = re.search(r'type[^\'"]*["\']([^"\']+)["\']', response, re.IGNORECASE)
            if type_match:
                text = type_match.group(1)
                # Try to find where to type
                in_match = re.search(r'in[^\'"]*["\']([^"\']+)["\']', response, re.IGNORECASE)
                if in_match:
                    return self.pilot.visual_type(in_match.group(1), text)
                else:
                    return self.pilot.type_text(text)
                    
        return ActionResult(success=False, error=f"Could not parse LLM response: {response}")