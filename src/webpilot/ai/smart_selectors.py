#!/usr/bin/env python3
"""
Smart Selectors - Auto-healing, resilient element selectors
Generates multiple fallback selectors and auto-heals when they break
"""

from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path


class SmartSelector:
    """Generate resilient selectors that survive DOM changes"""
    
    def __init__(self):
        """Initialize smart selector generator"""
        self.selector_cache_file = Path("selector_cache.json")
        self.selector_cache = self._load_cache()
        self.success_history: Dict[str, int] = {}
    
    def _load_cache(self) -> Dict:
        """Load selector cache from file"""
        if self.selector_cache_file.exists():
            with open(self.selector_cache_file) as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save selector cache to file"""
        with open(self.selector_cache_file, 'w') as f:
            json.dump(self.selector_cache, f, indent=2)
    
    def generate_selectors(self, page, description: str) -> List[Dict]:
        """
        Generate multiple fallback selectors for an element.
        
        Args:
            page: Playwright page object
            description: Human description of element (e.g., "sign in button")
            
        Returns:
            List of selector strategies, ordered by reliability
        """
        selectors = []
        
        # Strategy 1: Text content (most resilient)
        text_selector = f'text="{description}"'
        selectors.append({
            'type': 'text',
            'selector': text_selector,
            'priority': 1,
            'resilience': 'high',
            'description': f'Match by visible text: {description}'
        })
        
        # Strategy 2: Partial text match
        words = description.split()
        if words:
            partial_text = words[0]
            selectors.append({
                'type': 'text_partial',
                'selector': f'text=/{partial_text}/i',
                'priority': 2,
                'resilience': 'medium',
                'description': f'Match by partial text: {partial_text}'
            })
        
        # Strategy 3: Data attributes (very resilient)
        data_attrs = ['data-testid', 'data-test', 'data-cy']
        for attr in data_attrs:
            selectors.append({
                'type': 'data_attr',
                'selector': f'[{attr}*="{description.replace(" ", "-").lower()}"]',
                'priority': 1,
                'resilience': 'very_high',
                'description': f'Match by {attr}'
            })
        
        # Strategy 4: ARIA label
        selectors.append({
            'type': 'aria',
            'selector': f'[aria-label*="{description}"]',
            'priority': 2,
            'resilience': 'high',
            'description': 'Match by ARIA label'
        })
        
        # Strategy 5: Role + text
        common_roles = ['button', 'link', 'textbox', 'checkbox']
        for role in common_roles:
            selectors.append({
                'type': 'role_text',
                'selector': f'role={role}[name=/{description}/i]',
                'priority': 1,
                'resilience': 'high',
                'description': f'Match by {role} role and name'
            })
        
        return selectors
    
    def find_element(self, page, description: str) -> Optional[any]:
        """
        Find element using smart selector with auto-healing.
        
        Args:
            page: Playwright page object
            description: Human description of element
            
        Returns:
            Element locator or None
        """
        # Check cache first
        cache_key = f"{page.url}:{description}"
        if cache_key in self.selector_cache:
            cached_selector = self.selector_cache[cache_key]
            try:
                element = page.locator(cached_selector['selector'])
                if element.count() > 0:
                    print(f"✅ Found via cached selector: {cached_selector['selector']}")
                    self._record_success(cached_selector['selector'])
                    return element
                else:
                    print(f"⚠️  Cached selector failed, trying alternatives...")
            except Exception as e:
                print(f"⚠️  Cached selector error: {e}, trying alternatives...")
        
        # Generate and try selectors
        selectors = self.generate_selectors(page, description)
        
        # Sort by priority and success history
        selectors.sort(key=lambda s: (
            -s['priority'],
            -self.success_history.get(s['selector'], 0)
        ))
        
        # Try each selector
        for selector_info in selectors:
            try:
                element = page.locator(selector_info['selector'])
                count = element.count()
                
                if count == 1:
                    print(f"✅ Found via {selector_info['type']}: {selector_info['selector']}")
                    
                    # Cache successful selector
                    self.selector_cache[cache_key] = selector_info
                    self._save_cache()
                    self._record_success(selector_info['selector'])
                    
                    return element
                elif count > 1:
                    print(f"⚠️  Multiple matches ({count}) for: {selector_info['selector']}")
                    # Try next selector
            except Exception as e:
                # Try next selector
                pass
        
        print(f"❌ Could not find element: {description}")
        return None
    
    def generate_resilient_selector(self, page, element) -> str:
        """
        Generate most resilient selector for an element.
        
        Args:
            page: Playwright page object
            element: Element to generate selector for
            
        Returns:
            Best selector string
        """
        # Get element properties
        props = element.evaluate("""el => ({
            tag: el.tagName.toLowerCase(),
            id: el.id,
            classes: Array.from(el.classList),
            text: el.textContent.trim(),
            type: el.type,
            name: el.name,
            role: el.getAttribute('role'),
            ariaLabel: el.getAttribute('aria-label'),
            dataTestId: el.getAttribute('data-testid'),
            placeholder: el.getAttribute('placeholder')
        })""")
        
        # Priority 1: data-testid
        if props.get('dataTestId'):
            return f'[data-testid="{props["dataTestId"]}"]'
        
        # Priority 2: ID
        if props.get('id') and props['id']:
            return f'#{props["id"]}'
        
        # Priority 3: ARIA label
        if props.get('ariaLabel'):
            return f'[aria-label="{props["ariaLabel"]}"]'
        
        # Priority 4: Role + name
        if props.get('role') and props.get('text'):
            return f'role={props["role"]}[name="{props["text"][:30]}"]'
        
        # Priority 5: Text content
        if props.get('text') and len(props['text']) > 0:
            return f'text="{props["text"][:30]}"'
        
        # Fallback: tag + nth-of-type (least resilient)
        return f'{props["tag"]}'
    
    def auto_heal_selector(self, page, old_selector: str, description: str) -> Optional[str]:
        """
        Auto-heal a broken selector by finding element another way.
        
        Args:
            page: Playwright page object
            old_selector: Selector that no longer works
            description: What the element is/does
            
        Returns:
            New working selector or None
        """
        print(f"🔧 Auto-healing selector: {old_selector}")
        
        # Try to find element by description
        element = self.find_element(page, description)
        
        if element:
            # Generate new resilient selector
            new_selector = self.generate_resilient_selector(page, element.first)
            print(f"✅ Healed! New selector: {new_selector}")
            return new_selector
        
        print(f"❌ Could not heal selector")
        return None
    
    def _record_success(self, selector: str):
        """Record successful selector use"""
        self.success_history[selector] = self.success_history.get(selector, 0) + 1
    
    def get_selector_stats(self) -> Dict:
        """Get statistics about selector usage"""
        return {
            'total_cached': len(self.selector_cache),
            'most_successful': sorted(
                self.success_history.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def recommend_test_ids(self, page) -> List[Dict]:
        """
        Recommend where to add data-testid attributes.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of elements that should have test IDs
        """
        recommendations = []
        
        # Check interactive elements without test IDs
        interactive = page.query_selector_all('''
            button:not([data-testid]),
            a:not([data-testid]),
            input:not([data-testid]),
            select:not([data-testid]),
            textarea:not([data-testid])
        ''')
        
        for i, el in enumerate(interactive[:20]):  # Limit to 20
            try:
                tag = el.evaluate('el => el.tagName.toLowerCase()')
                text = el.inner_text()[:30] if el.inner_text() else 'no text'
                selector = el.evaluate('''el => {
                    let path = el.tagName.toLowerCase();
                    if (el.id) path += '#' + el.id;
                    if (el.className) path += '.' + el.className.split(' ')[0];
                    return path;
                }''')
                
                recommendations.append({
                    'element': tag,
                    'text': text,
                    'current_selector': selector,
                    'suggested_test_id': f'{tag}-{i}',
                    'reason': 'Interactive element without test ID'
                })
            except:
                pass
        
        return recommendations


# Quick usage functions
def find_element(page, description: str):
    """Quick function to find element smartly"""
    smart = SmartSelector()
    return smart.find_element(page, description)


def heal_selector(page, old_selector: str, description: str) -> Optional[str]:
    """Quick function to heal broken selector"""
    smart = SmartSelector()
    return smart.auto_heal_selector(page, old_selector, description)


# Example usage
if __name__ == "__main__":
    print("🧠 Smart Selectors Demo\n")
    print("This module creates resilient, auto-healing selectors.")
    print("\nFeatures:")
    print("  • Multiple fallback strategies")
    print("  • Auto-healing when selectors break")
    print("  • Learning from success/failure")
    print("  • Caching for performance")
    print("\nUsage:")
    print('  smart = SmartSelector()')
    print('  element = smart.find_element(page, "sign in button")')
    print('  if element:')
    print('      element.click()')
