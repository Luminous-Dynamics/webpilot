#!/usr/bin/env python
"""
Natural Language Test Generation Examples

Shows how to use WebPilot's natural language test generation with various LLMs.
"""

import asyncio
import json
from typing import List, Dict, Any
from webpilot.testing.natural_language_tests import (
    NaturalLanguageTestGenerator,
    TestFramework,
    Language,
    SmartTestRecorder
)


# Example 1: Simple Natural Language to Test Code
def example_basic_test_generation():
    """Generate test code from simple natural language description."""
    
    print("=" * 60)
    print("Example 1: Basic Test Generation")
    print("=" * 60)
    
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    # Natural language test description
    test_description = """
    Test: Search for Python tutorials on Google
    
    Steps:
    1. Go to google.com
    2. Type "Python tutorials" in the search box
    3. Click the search button
    4. Wait for results to load
    
    Verify:
    - The page contains "Python"
    - At least 10 results are shown
    """
    
    # Generate test case
    test_case = generator.parse_natural_language(test_description)
    
    # Create test suite
    test_suite = generator.generate_test_suite(
        [test_description],
        suite_name="GoogleSearchTests"
    )
    
    # Generate code
    code = generator.generate_code(test_suite)
    print("\nGenerated pytest code:")
    print(code)


# Example 2: E-commerce Test Suite
def example_ecommerce_tests():
    """Generate comprehensive e-commerce test suite."""
    
    print("\n" + "=" * 60)
    print("Example 2: E-commerce Test Suite")
    print("=" * 60)
    
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PLAYWRIGHT,
        language=Language.PYTHON
    )
    
    test_descriptions = [
        """
        Test: Add product to cart
        
        Given:
        - User is on the product page
        
        When:
        - Click "Add to Cart" button
        - Click "View Cart"
        
        Then:
        - Cart should contain 1 item
        - Total price should be displayed
        """,
        
        """
        Test: Checkout process
        
        Setup:
        - Navigate to checkout page
        
        Steps:
        - Fill "email" field with "customer@example.com"
        - Fill "name" field with "John Doe"
        - Fill "address" field with "123 Main St"
        - Select "Credit Card" from payment method
        - Click "Place Order"
        
        Assertions:
        - Order confirmation is visible
        - Order number is displayed
        """,
        
        """
        Test: Search and filter products
        
        1. Go to shop.example.com
        2. Type "laptop" in search field
        3. Click search button
        4. Select "Price: Low to High" from sort dropdown
        5. Click on first product
        
        Verify that product details page is displayed
        Verify that price is shown
        """
    ]
    
    # Generate test suite
    test_suite = generator.generate_test_suite(
        test_descriptions,
        suite_name="EcommerceTests"
    )
    
    # Generate code
    code = generator.generate_code(test_suite)
    print("\nGenerated Playwright code:")
    print(code[:1000])  # First 1000 chars
    
    # Also generate Page Object
    page_object = generator.generate_page_object(test_suite.test_cases)
    print("\n\nGenerated Page Object Model:")
    print(page_object)


# Example 3: Multi-Framework Generation
def example_multi_framework():
    """Generate same test for multiple frameworks."""
    
    print("\n" + "=" * 60)
    print("Example 3: Multi-Framework Generation")
    print("=" * 60)
    
    test_description = """
    Test: User registration
    
    1. Navigate to https://app.example.com/register
    2. Enter "newuser@example.com" in email field
    3. Enter "SecurePass123!" in password field
    4. Enter "SecurePass123!" in confirm password field
    5. Check the terms checkbox
    6. Click "Create Account" button
    
    Verify account created successfully message appears
    """
    
    frameworks = [
        (TestFramework.PYTEST, Language.PYTHON, "pytest"),
        (TestFramework.JEST, Language.JAVASCRIPT, "Jest"),
        (TestFramework.CYPRESS, Language.JAVASCRIPT, "Cypress"),
        (TestFramework.PLAYWRIGHT, Language.TYPESCRIPT, "Playwright TS")
    ]
    
    for framework, language, name in frameworks:
        print(f"\n{name} version:")
        print("-" * 40)
        
        generator = NaturalLanguageTestGenerator(
            framework=framework,
            language=language
        )
        
        test_suite = generator.generate_test_suite(
            [test_description],
            suite_name="RegistrationTests"
        )
        
        code = generator.generate_code(test_suite)
        print(code[:500])  # First 500 chars


# Example 4: LLM-Powered Test Generation
def example_llm_test_generation():
    """Use LLM to generate tests from user stories."""
    
    print("\n" + "=" * 60)
    print("Example 4: LLM-Powered Test Generation")
    print("=" * 60)
    
    # This would connect to an actual LLM
    # Here we simulate the LLM response
    
    user_story = """
    As a user, I want to reset my password
    so that I can regain access to my account if I forget it.
    
    Acceptance Criteria:
    - User can request password reset from login page
    - Email with reset link is sent
    - User can set new password using the link
    - User can login with new password
    """
    
    # Simulate LLM converting user story to test cases
    def llm_generate_tests(story: str) -> List[str]:
        """Simulate LLM generating test descriptions."""
        # In reality, this would call OpenAI, Ollama, etc.
        return [
            """
            Test: Request password reset
            1. Go to login page
            2. Click "Forgot Password?" link
            3. Enter "user@example.com" in email field
            4. Click "Send Reset Email"
            Verify: Success message "Reset email sent" is displayed
            """,
            
            """
            Test: Reset password with valid link
            1. Navigate to reset link from email
            2. Enter "NewPassword123!" in new password field
            3. Enter "NewPassword123!" in confirm password field
            4. Click "Reset Password"
            Verify: "Password successfully reset" message appears
            """,
            
            """
            Test: Login with new password
            1. Go to login page
            2. Enter "user@example.com" in email field
            3. Enter "NewPassword123!" in password field
            4. Click "Login"
            Verify: User is redirected to dashboard
            """
        ]
    
    print(f"User Story:\n{user_story}\n")
    
    # Generate test descriptions via LLM
    test_descriptions = llm_generate_tests(user_story)
    
    print("LLM Generated Test Cases:")
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\nTest Case {i}:")
        print(desc.strip())
    
    # Convert to executable tests
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    test_suite = generator.generate_test_suite(
        test_descriptions,
        suite_name="PasswordResetTests"
    )
    
    code = generator.generate_code(test_suite)
    
    print("\n\nGenerated Executable Test Code:")
    print("=" * 40)
    print(code)


# Example 5: Recording and Learning
async def example_test_recording():
    """Record user interactions and generate tests."""
    
    print("\n" + "=" * 60)
    print("Example 5: Test Recording and Learning")
    print("=" * 60)
    
    from webpilot import WebPilot
    
    # Create recorder
    pilot = WebPilot(headless=True)
    recorder = SmartTestRecorder(pilot)
    
    # Simulate recording user interactions
    print("Simulating user interactions...")
    
    recorder.start_recording()
    
    # Simulate actions (in real use, these would be actual user interactions)
    recorder.record_action('navigate', url='https://example.com')
    recorder.record_action('click', text='Products', selector='#nav-products')
    recorder.record_action('type', text='laptop', selector='#search-box')
    recorder.record_action('click', text='Search', selector='#search-btn')
    recorder.record_action('click', text='First Product', selector='.product-item:first')
    recorder.record_action('click', text='Add to Cart', selector='#add-to-cart')
    recorder.record_action('screenshot')
    
    recording = recorder.stop_recording()
    
    print(f"\nRecorded {len(recording)} interactions")
    
    # Generate test from recording
    test_code = recorder.generate_test_from_recording(
        name="test_product_purchase_flow",
        framework=TestFramework.PYTEST
    )
    
    print("\nGenerated test from recording:")
    print(test_code)
    
    # Learn patterns
    patterns = recorder.learn_patterns()
    print("\n\nLearned patterns:")
    print(f"Action frequency: {patterns['action_frequency']}")
    
    pilot.close()


# Example 6: Data-Driven Testing
def example_data_driven_tests():
    """Generate data-driven tests with multiple test data sets."""
    
    print("\n" + "=" * 60)
    print("Example 6: Data-Driven Testing")
    print("=" * 60)
    
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    # Test with parameters
    test_template = """
    Test: Login with {username} and {password}
    
    1. Go to login page
    2. Enter "{username}" in username field
    3. Enter "{password}" in password field
    4. Click login button
    
    Verify: {expected_result}
    """
    
    test_data = [
        {
            'username': 'valid@example.com',
            'password': 'correct123',
            'expected_result': 'Dashboard is displayed'
        },
        {
            'username': 'invalid@example.com',
            'password': 'wrong',
            'expected_result': 'Error message is shown'
        },
        {
            'username': '',
            'password': '',
            'expected_result': 'Required field errors appear'
        }
    ]
    
    # Generate tests for each data set
    test_descriptions = []
    for data in test_data:
        test_desc = test_template.format(**data)
        test_descriptions.append(test_desc)
    
    # Create test suite
    test_suite = generator.generate_test_suite(
        test_descriptions,
        suite_name="DataDrivenLoginTests"
    )
    
    # Generate parametrized test code
    code = generator.generate_code(test_suite)
    
    print("Generated data-driven tests:")
    print(code)
    
    # Also show how to generate with pytest parametrize
    print("\n\nParametrized version:")
    print("""
import pytest
from webpilot import WebPilot

@pytest.mark.parametrize("username,password,expected", [
    ("valid@example.com", "correct123", "Dashboard"),
    ("invalid@example.com", "wrong", "Error"),
    ("", "", "Required field"),
])
def test_login_scenarios(pilot, username, password, expected):
    pilot.navigate("https://example.com/login")
    pilot.type_text(username, selector="#username")
    pilot.type_text(password, selector="#password")
    pilot.click(selector="#login-btn")
    
    page_content = pilot.get_page_source()
    assert expected in page_content
    """)


# Example 7: BDD-Style Tests
def example_bdd_tests():
    """Generate BDD-style tests from Gherkin-like descriptions."""
    
    print("\n" + "=" * 60)
    print("Example 7: BDD-Style Test Generation")
    print("=" * 60)
    
    generator = NaturalLanguageTestGenerator(
        framework=TestFramework.PYTEST,
        language=Language.PYTHON
    )
    
    bdd_scenario = """
    Test: Customer can purchase a product
    
    Given: I am on the shopping website
    And: I am logged in as "customer@example.com"
    
    When: I search for "wireless headphones"
    And: I click on the first product
    And: I click "Add to Cart"
    And: I click "Checkout"
    And: I enter my payment details
    And: I click "Complete Purchase"
    
    Then: I should see "Order Confirmed"
    And: I should receive an order number
    And: The order should appear in my account
    """
    
    test_case = generator.parse_natural_language(bdd_scenario)
    
    # Generate both pytest and Cucumber-style output
    test_suite = generator.generate_test_suite(
        [bdd_scenario],
        suite_name="BDDPurchaseTests"
    )
    
    pytest_code = generator.generate_code(test_suite)
    
    print("Generated pytest code:")
    print(pytest_code)
    
    print("\n\nCucumber feature file equivalent:")
    print("""
Feature: Product Purchase
  As a customer
  I want to purchase products
  So that I can receive them

  Scenario: Customer can purchase a product
    Given I am on the shopping website
    And I am logged in as "customer@example.com"
    When I search for "wireless headphones"
    And I click on the first product
    And I click "Add to Cart"
    And I click "Checkout"
    And I enter my payment details
    And I click "Complete Purchase"
    Then I should see "Order Confirmed"
    And I should receive an order number
    And The order should appear in my account
    """)


# Main execution
def main():
    """Run all examples."""
    
    print("WebPilot Natural Language Test Generation Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_test_generation()
    example_ecommerce_tests()
    example_multi_framework()
    example_llm_test_generation()
    
    # Run async example
    print("\nRunning async recording example...")
    asyncio.run(example_test_recording())
    
    example_data_driven_tests()
    example_bdd_tests()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nYou can now:")
    print("1. Use natural language to describe tests")
    print("2. Generate tests for any framework")
    print("3. Record and learn from user interactions")
    print("4. Create data-driven tests")
    print("5. Generate BDD-style scenarios")


if __name__ == "__main__":
    main()