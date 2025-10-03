"""
Natural Language Processing for WebPilot
Converts plain English commands to automation actions
"""

import re
from typing import Dict, List, Any


class NaturalLanguageProcessor:
    """Convert natural language to automation commands."""
    
    def __init__(self):
        self.command_patterns = {
            'navigate': [
                r'(?:go to|navigate to|visit|open)\s+(.+)',
                r'(?:load|browse to)\s+(.+)',
            ],
            'click': [
                r'(?:click|press|tap)\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'(?:select|choose)\s+(?:the\s+)?(.+)',
            ],
            'type': [
                r'(?:type|enter|write|fill)\s+["\']([^"\']+)["\']',
                r'(?:input|put)\s+["\']([^"\']+)["\']',
            ],
            'search': [
                r'search\s+(?:for\s+)?["\']?([^"\']+)["\']?',
                r'find\s+["\']?([^"\']+)["\']?',
            ],
            'verify': [
                r'(?:verify|check|assert|ensure)\s+(?:that\s+)?(.+)',
                r'(?:should|must)\s+(?:have|contain|show)\s+(.+)',
            ],
            'screenshot': [
                r'(?:take|capture|grab)\s+(?:a\s+)?screenshot',
                r'screenshot(?:\s+the\s+page)?',
            ],
            'wait': [
                r'wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)?',
                r'pause\s+(?:for\s+)?(\d+)',
            ]
        }
        
        # Learning from usage
        self.learned_patterns = []
        self.success_history = []
    
    def parse(self, command: str) -> Dict[str, Any]:
        """Parse natural language command into structured action."""
        command_lower = command.lower().strip()
        
        # Check each command type
        for action_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    return self._create_action(action_type, match, command)
        
        # If no pattern matched, use AI-like heuristics
        return self._smart_parse(command)
    
    def _create_action(self, action_type: str, match, original_command: str) -> Dict:
        """Create structured action from regex match."""
        if action_type == 'navigate':
            url = match.group(1).strip()
            if not url.startswith('http'):
                url = f'https://{url}'
            return {
                'action': 'navigate',
                'url': url,
                'original': original_command,
                'confidence': 0.95
            }
        
        elif action_type == 'click':
            target = match.group(1).strip()
            return {
                'action': 'click',
                'target': target,
                'selectors': self._generate_selectors(target),
                'original': original_command,
                'confidence': 0.85
            }
        
        elif action_type == 'type':
            text = match.group(1)
            return {
                'action': 'type',
                'text': text,
                'original': original_command,
                'confidence': 0.90
            }
        
        elif action_type == 'search':
            query = match.group(1).strip()
            return {
                'action': 'search',
                'query': query,
                'original': original_command,
                'confidence': 0.88
            }
        
        elif action_type == 'verify':
            condition = match.group(1).strip()
            return {
                'action': 'verify',
                'condition': condition,
                'original': original_command,
                'confidence': 0.80
            }
            
        elif action_type == 'screenshot':
            return {
                'action': 'screenshot',
                'original': original_command,
                'confidence': 0.95
            }
            
        elif action_type == 'wait':
            duration = int(match.group(1))
            return {
                'action': 'wait',
                'duration': duration,
                'original': original_command,
                'confidence': 0.95
            }
        
        return {'action': 'unknown', 'original': original_command, 'confidence': 0.0}
    
    def _smart_parse(self, command: str) -> Dict:
        """Use smart heuristics when patterns don't match."""
        command_lower = command.lower()
        
        # URL detection
        if any(x in command_lower for x in ['.com', '.org', 'www.', 'http']):
            url_match = re.search(r'([a-z]+\.[a-z]{2,}[^\s]*)', command_lower)
            if url_match:
                return {
                    'action': 'navigate',
                    'url': f'https://{url_match.group(1)}',
                    'original': command,
                    'confidence': 0.70
                }
        
        # Button/Link detection
        if any(x in command_lower for x in ['button', 'link', 'menu', 'tab']):
            target = command_lower
            for word in ['click', 'press', 'the', 'on', 'button', 'link']:
                target = target.replace(word, '').strip()
            return {
                'action': 'click',
                'target': target,
                'selectors': self._generate_selectors(target),
                'original': command,
                'confidence': 0.65
            }
        
        # Form field detection
        if any(x in command_lower for x in ['field', 'input', 'textbox', 'form']):
            text_match = re.search(r'["\']([^"\']+)["\']', command)
            if text_match:
                return {
                    'action': 'type',
                    'text': text_match.group(1),
                    'original': command,
                    'confidence': 0.60
                }
        
        return {
            'action': 'unknown',
            'original': command,
            'confidence': 0.0,
            'suggestion': 'Try rephrasing. Examples: "Go to google.com", "Click the login button", "Type \'hello\' in search"'
        }
    
    def _generate_selectors(self, target: str) -> List[str]:
        """Generate multiple selector strategies for an element."""
        selectors = []
        
        # Clean the target
        clean_target = target.strip().lower()
        
        # Text-based selectors
        selectors.append(f"//button[contains(text(), '{target}')]")
        selectors.append(f"//a[contains(text(), '{target}')]")
        selectors.append(f"//*[text()='{target}']")
        
        # Attribute-based selectors
        selectors.append(f"//button[@aria-label*='{clean_target}']")
        selectors.append(f"//input[@placeholder*='{clean_target}']")
        selectors.append(f"//*[@title*='{clean_target}']")
        
        # ID and class selectors
        snake_case = clean_target.replace(' ', '_').replace('-', '_')
        kebab_case = clean_target.replace(' ', '-').replace('_', '-')
        
        selectors.append(f"#{snake_case}")
        selectors.append(f"#{kebab_case}")
        selectors.append(f".{snake_case}")
        selectors.append(f".{kebab_case}")
        selectors.append(f"[data-testid='{kebab_case}']")
        
        return selectors
    
    def learn_from_success(self, command: str, action: Dict):
        """Learn from successful command execution."""
        self.success_history.append({
            'command': command,
            'action': action,
            'timestamp': 'now'
        })
        
        # Could implement pattern learning from successes in future
        return True