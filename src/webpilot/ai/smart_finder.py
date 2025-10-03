"""
Smart Element Finding with Self-Healing
Finds elements using multiple strategies and learns from successes
"""

from typing import Dict, List, Optional


class SmartElementFinder:
    """Find elements using multiple strategies with self-healing."""
    
    def __init__(self):
        self.selector_history = {}
        self.healing_strategies = [
            self._try_exact_text,
            self._try_partial_text,
            self._try_fuzzy_match,
            self._try_attribute_match,
            self._try_visual_similarity,
            self._try_position_based,
        ]
    
    def find(self, description: str, previous_selector: Optional[str] = None) -> Dict:
        """Find element with self-healing capabilities."""
        result = {
            'found': False,
            'selector': None,
            'confidence': 0.0,
            'strategy': None,
            'alternatives': []
        }
        
        # Try previous selector first (if available and successful before)
        if previous_selector and previous_selector in self.selector_history:
            if self.selector_history[previous_selector]['success_rate'] > 0.7:
                result['selector'] = previous_selector
                result['confidence'] = 0.9
                result['strategy'] = 'cached'
                result['found'] = True
                return result
        
        # Try each healing strategy
        for strategy in self.healing_strategies:
            strategy_result = strategy(description)
            if strategy_result['confidence'] > result['confidence']:
                result = strategy_result
                if result['confidence'] > 0.8:
                    break
        
        # Update history
        if result['found'] and result['selector']:
            self._update_history(result['selector'], success=True)
        
        return result
    
    def _try_exact_text(self, description: str) -> Dict:
        """Try exact text matching."""
        return {
            'found': True,
            'selector': f"//button[text()='{description}']",
            'confidence': 0.95,
            'strategy': 'exact_text',
            'alternatives': [
                f"//a[text()='{description}']",
                f"//span[text()='{description}']"
            ]
        }
    
    def _try_partial_text(self, description: str) -> Dict:
        """Try partial text matching."""
        return {
            'found': True,
            'selector': f"//*[contains(text(), '{description}')]",
            'confidence': 0.85,
            'strategy': 'partial_text',
            'alternatives': [
                f"//button[contains(text(), '{description}')]",
                f"//a[contains(text(), '{description}')]"
            ]
        }
    
    def _try_fuzzy_match(self, description: str) -> Dict:
        """Try fuzzy matching with common variations."""
        variations = [
            description.lower(),
            description.upper(),
            description.title(),
            description.replace(' ', ''),
            description.replace(' ', '-'),
            description.replace(' ', '_'),
        ]
        
        selectors = []
        for var in variations[:3]:  # Limit to prevent too many options
            selectors.append(f"//*[contains(@*, '{var}')]")
        
        return {
            'found': True,
            'selector': selectors[0] if selectors else f"//*[contains(@*, '{description.lower()}')]",
            'confidence': 0.70,
            'strategy': 'fuzzy_match',
            'alternatives': selectors[1:] if len(selectors) > 1 else []
        }
    
    def _try_attribute_match(self, description: str) -> Dict:
        """Try matching common attributes."""
        clean_desc = description.lower().strip()
        
        return {
            'found': True,
            'selector': f"//*[@aria-label*='{clean_desc}']",
            'confidence': 0.75,
            'strategy': 'attribute_match',
            'alternatives': [
                f"//*[@title*='{clean_desc}']",
                f"//*[@placeholder*='{clean_desc}']",
                f"//*[@alt*='{clean_desc}']",
                f"//*[@data-testid*='{clean_desc.replace(' ', '-')}']"
            ]
        }
    
    def _try_visual_similarity(self, description: str) -> Dict:
        """Simulate visual similarity matching."""
        # In real implementation, this would use computer vision
        # For now, we'll use common UI patterns
        
        if 'button' in description.lower():
            selector = "//button[contains(@class, 'btn')]"
        elif 'link' in description.lower():
            selector = "//a[contains(@class, 'link')]"
        elif 'input' in description.lower() or 'field' in description.lower():
            selector = "//input[@type='text']"
        else:
            selector = f"//*[contains(@class, '{description.split()[0].lower()}')]"
            
        return {
            'found': True,
            'selector': selector,
            'confidence': 0.60,
            'strategy': 'visual_similarity',
            'alternatives': []
        }
    
    def _try_position_based(self, description: str) -> Dict:
        """Try position-based selection as last resort."""
        # This is a fallback when nothing else works
        
        if 'first' in description.lower():
            position = 1
        elif 'last' in description.lower():
            position = 'last()'
        elif 'second' in description.lower():
            position = 2
        else:
            position = 1
            
        return {
            'found': True,
            'selector': f"(//button)[{position}]",
            'confidence': 0.50,
            'strategy': 'position_based',
            'alternatives': [
                f"(//a)[{position}]",
                f"(//input)[{position}]"
            ]
        }
    
    def _update_history(self, selector: str, success: bool):
        """Update selector success history for learning."""
        if selector not in self.selector_history:
            self.selector_history[selector] = {
                'attempts': 0,
                'successes': 0,
                'success_rate': 0.0
            }
        
        self.selector_history[selector]['attempts'] += 1
        if success:
            self.selector_history[selector]['successes'] += 1
        
        self.selector_history[selector]['success_rate'] = (
            self.selector_history[selector]['successes'] / 
            self.selector_history[selector]['attempts']
        )
    
    def get_best_selector_for(self, description: str) -> str:
        """Get the best known selector for a description."""
        result = self.find(description)
        return result['selector'] if result['found'] else None
    
    def report_healing(self) -> Dict:
        """Generate a healing report."""
        return {
            'total_selectors': len(self.selector_history),
            'successful_selectors': sum(1 for s in self.selector_history.values() 
                                       if s['success_rate'] > 0.7),
            'healing_rate': sum(s['success_rate'] for s in self.selector_history.values()) / 
                           max(len(self.selector_history), 1),
            'top_strategies': self._get_top_strategies()
        }
    
    def _get_top_strategies(self) -> List[str]:
        """Get most successful strategies."""
        # This would analyze history to find best strategies
        # For now, return default order
        return ['exact_text', 'partial_text', 'attribute_match']