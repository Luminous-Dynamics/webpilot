"""
Simple AI Integration for WebPilot v1.x
Adds natural language capabilities to existing WebPilot
"""

from typing import Dict, Any, Optional
from .natural_language import NaturalLanguageProcessor
from .smart_finder import SmartElementFinder


class SimpleAI:
    """
    Simple AI layer that adds natural language to WebPilot v1.x
    This is pragmatic and ships today!
    """
    
    def __init__(self, webpilot_instance=None):
        """
        Initialize with optional WebPilot instance.
        Can work standalone for NLP or with WebPilot for execution.
        """
        self.pilot = webpilot_instance
        self.nlp = NaturalLanguageProcessor()
        self.finder = SmartElementFinder()
        self.command_history = []
        
    def execute(self, natural_language_command: str) -> Dict[str, Any]:
        """
        Execute a natural language command.
        Works with or without WebPilot instance.
        """
        # Parse the command
        parsed = self.nlp.parse(natural_language_command)
        
        # Store in history
        self.command_history.append({
            'command': natural_language_command,
            'parsed': parsed
        })
        
        # If no WebPilot instance, return parsed command
        if not self.pilot:
            return {
                'success': True,
                'action': parsed,
                'message': f"Parsed as {parsed['action']} with {parsed['confidence']*100:.0f}% confidence"
            }
        
        # Execute with WebPilot
        return self._execute_with_pilot(parsed)
    
    def _execute_with_pilot(self, action: Dict) -> Dict[str, Any]:
        """Execute parsed action using WebPilot instance."""
        try:
            if action['action'] == 'navigate':
                self.pilot.navigate(action['url'])
                return {'success': True, 'message': f"Navigated to {action['url']}"}
                
            elif action['action'] == 'click':
                # Use smart finder to get best selector
                element_info = self.finder.find(action['target'])
                if element_info['found']:
                    # Try primary selector
                    success = self._try_click(element_info['selector'])
                    
                    # If failed, try alternatives
                    if not success and element_info.get('alternatives'):
                        for alt_selector in element_info['alternatives']:
                            if self._try_click(alt_selector):
                                success = True
                                break
                    
                    if success:
                        self.finder._update_history(element_info['selector'], True)
                        return {'success': True, 'message': f"Clicked {action['target']}"}
                    else:
                        return {'success': False, 'message': f"Could not click {action['target']}"}
                else:
                    return {'success': False, 'message': f"Could not find {action['target']}"}
                    
            elif action['action'] == 'type':
                self.pilot.type_text(action['text'])
                return {'success': True, 'message': f"Typed '{action['text']}'"}
                
            elif action['action'] == 'screenshot':
                filename = self.pilot.screenshot()
                return {'success': True, 'message': f"Screenshot saved", 'filename': filename}
                
            elif action['action'] == 'wait':
                import time
                time.sleep(action['duration'])
                return {'success': True, 'message': f"Waited {action['duration']} seconds"}
                
            elif action['action'] == 'verify':
                # Simple text verification
                page_text = self.pilot.get_page_text() if hasattr(self.pilot, 'get_page_text') else ""
                if action['condition'].lower() in page_text.lower():
                    return {'success': True, 'message': "Verification passed"}
                else:
                    return {'success': False, 'message': "Verification failed"}
                    
            else:
                return {
                    'success': False, 
                    'message': f"Unknown action: {action['action']}",
                    'suggestion': action.get('suggestion', '')
                }
                
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
    
    def _try_click(self, selector: str) -> bool:
        """Try to click using a selector."""
        try:
            # Try different click methods based on what WebPilot supports
            if hasattr(self.pilot, 'click_xpath'):
                self.pilot.click_xpath(selector)
                return True
            elif hasattr(self.pilot, 'click'):
                self.pilot.click(selector)
                return True
            else:
                # Fallback to generic click if available
                element = self.pilot.find_element(selector)
                if element:
                    element.click()
                    return True
        except:
            pass
        return False
    
    def suggest_next_action(self, context: str = "") -> str:
        """
        Suggest next action based on history and context.
        This is where we could add ML in the future.
        """
        if not self.command_history:
            return "Try: 'Go to example.com' or 'Click the search button'"
        
        last_command = self.command_history[-1]
        if last_command['parsed']['action'] == 'navigate':
            return "Try clicking on something or typing text"
        elif last_command['parsed']['action'] == 'click':
            return "Try typing something or taking a screenshot"
        else:
            return "Try navigating to a page or clicking a button"
    
    def get_healing_report(self) -> Dict:
        """Get report on self-healing performance."""
        return self.finder.report_healing()
    
    def learn_from_success(self, command: str):
        """Mark a command as successful for learning."""
        if self.command_history:
            last_parsed = self.command_history[-1]['parsed']
            self.nlp.learn_from_success(command, last_parsed)
            
    def batch_execute(self, commands: list) -> list:
        """Execute multiple commands in sequence."""
        results = []
        for command in commands:
            result = self.execute(command)
            results.append({
                'command': command,
                'result': result
            })
            
            # Stop on failure unless it's a verify command
            if not result['success'] and 'verify' not in command.lower():
                break
                
        return results