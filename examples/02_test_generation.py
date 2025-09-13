#!/usr/bin/env python3
"""
WebPilot ML-Powered Test Generation Example

This example demonstrates how to:
- Record user interactions
- Learn patterns from sessions
- Generate test code automatically
- Train the ML model for better predictions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot import WebPilot
from webpilot.ml.test_generator import (
    IntelligentTestGenerator,
    PatternDetector,
    TestPredictor,
    UserAction,
    ActionType
)


def record_manual_session():
    """Record a manual testing session."""
    print("📹 Recording Manual Testing Session")
    print("=" * 50)
    
    with WebPilot() as pilot:
        # Start recording
        pilot.session.start_recording()
        
        # Perform manual actions
        print("\nPerforming manual test actions...")
        
        # Navigate to test site
        pilot.start("https://example.com")
        print("✅ Navigated to example.com")
        
        # Click on a link (simulated)
        pilot.click(text="More information")
        print("✅ Clicked 'More information' link")
        
        # Take screenshot
        pilot.screenshot("test_screenshot.png")
        print("✅ Captured screenshot")
        
        # Save session
        session_file = Path("manual_session.json")
        pilot.session.save(session_file)
        print(f"\n✅ Session saved to {session_file}")
        
        return session_file


def generate_tests_from_session(session_file):
    """Generate tests from a recorded session."""
    print("\n🤖 Generating Tests from Session")
    print("=" * 50)
    
    # Initialize test generator
    generator = IntelligentTestGenerator()
    
    # Learn patterns from session
    print(f"\nLearning from {session_file}...")
    patterns = generator.learn_from_session(session_file)
    
    print(f"✅ Discovered {len(patterns)} test patterns")
    
    # Display discovered patterns
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern.name}")
        print(f"  - Actions: {len(pattern.actions)}")
        print(f"  - Frequency: {pattern.frequency}")
        print(f"  - Confidence: {pattern.confidence:.2f}")
        print(f"  - Category: {pattern.category}")
    
    # Generate test code
    output_dir = Path("generated_tests")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\nGenerating test code to {output_dir}/...")
    generator.export_tests(output_dir, language="python")
    
    # Also generate JavaScript tests
    generator.export_tests(output_dir, language="javascript")
    
    print("✅ Test files generated:")
    for test_file in output_dir.glob("test_*.py"):
        print(f"  - {test_file.name}")
    for test_file in output_dir.glob("test_*.js"):
        print(f"  - {test_file.name}")
    
    return patterns


def demonstrate_pattern_detection():
    """Demonstrate pattern detection capabilities."""
    print("\n🔍 Pattern Detection Demonstration")
    print("=" * 50)
    
    # Create sample user actions
    sample_actions = [
        # Login pattern (repeated)
        UserAction(ActionType.NAVIGATE, url="https://app.example.com"),
        UserAction(ActionType.CLICK, selector="#login-button"),
        UserAction(ActionType.TYPE, selector="#username", text="user1"),
        UserAction(ActionType.TYPE, selector="#password", text="pass123"),
        UserAction(ActionType.CLICK, selector="#submit"),
        UserAction(ActionType.WAIT, selector=".dashboard"),
        
        # Same pattern with different user
        UserAction(ActionType.NAVIGATE, url="https://app.example.com"),
        UserAction(ActionType.CLICK, selector="#login-button"),
        UserAction(ActionType.TYPE, selector="#username", text="user2"),
        UserAction(ActionType.TYPE, selector="#password", text="pass456"),
        UserAction(ActionType.CLICK, selector="#submit"),
        UserAction(ActionType.WAIT, selector=".dashboard"),
        
        # Search pattern
        UserAction(ActionType.CLICK, selector="#search-icon"),
        UserAction(ActionType.TYPE, selector="#search-input", text="test query"),
        UserAction(ActionType.CLICK, selector="#search-submit"),
        UserAction(ActionType.WAIT, selector=".results"),
    ]
    
    # Detect patterns
    detector = PatternDetector(min_pattern_length=3, min_frequency=2)
    patterns = detector.detect_patterns(sample_actions)
    
    print(f"\n✅ Detected {len(patterns)} patterns from {len(sample_actions)} actions")
    
    # Generate test code for first pattern
    if patterns:
        pattern = patterns[0]
        print(f"\nPattern: {pattern.name}")
        print("\nGenerated Python Test:")
        print("-" * 40)
        test_code = pattern.to_test_code("python")
        print(test_code[:500] + "..." if len(test_code) > 500 else test_code)
        
        print("\nGenerated JavaScript Test:")
        print("-" * 40)
        js_code = pattern.to_test_code("javascript")
        print(js_code[:500] + "..." if len(js_code) > 500 else js_code)


def demonstrate_test_prediction():
    """Demonstrate ML-based test prediction."""
    print("\n🔮 Test Prediction Demonstration")
    print("=" * 50)
    
    # Create training data
    training_actions = [
        UserAction(ActionType.NAVIGATE, url="https://example.com"),
        UserAction(ActionType.CLICK, selector="#login"),
        UserAction(ActionType.TYPE, selector="#username", text="test"),
        UserAction(ActionType.TYPE, selector="#password", text="pass"),
        UserAction(ActionType.CLICK, selector="#submit"),
        UserAction(ActionType.WAIT, selector=".dashboard"),
    ]
    
    # Create predictor
    predictor = TestPredictor()
    
    # Prepare training data
    training_data = []
    for i in range(3, len(training_actions)):
        context = training_actions[:i]
        next_action = training_actions[i]
        training_data.append((context, next_action))
    
    # Train model
    print("\nTraining prediction model...")
    predictor.train(training_data * 10)  # Duplicate for more training data
    
    # Make predictions
    test_context = training_actions[:3]
    print("\nContext actions:")
    for action in test_context:
        print(f"  - {action.action_type.name}: {action.selector or action.url or action.text}")
    
    predicted_action, confidence = predictor.predict_next_action(test_context)
    print(f"\n✅ Predicted next action: {predicted_action.name}")
    print(f"   Confidence: {confidence:.2%}")
    
    # Suggest test completion
    print("\nSuggesting test completion...")
    suggested_actions = predictor.suggest_test_completion(test_context, max_steps=3)
    
    print(f"✅ Suggested {len(suggested_actions)} additional actions:")
    for action in suggested_actions:
        print(f"  - {action.action_type.name}")


def generate_test_report(generator):
    """Generate a report of discovered patterns."""
    print("\n📊 Generating Test Report")
    print("=" * 50)
    
    report = generator.generate_test_report()
    
    print(f"\nTest Generation Report")
    print(f"Generated at: {report['timestamp']}")
    print(f"Total patterns discovered: {report['total_patterns']}")
    
    if report['categories']:
        print("\nPatterns by category:")
        for category, count in report['categories'].items():
            print(f"  - {category}: {count}")
    
    if report['patterns']:
        print("\nTop patterns by confidence:")
        sorted_patterns = sorted(
            report['patterns'],
            key=lambda x: x['confidence'],
            reverse=True
        )[:5]
        
        for pattern in sorted_patterns:
            print(f"  - {pattern['name']}: {pattern['confidence']:.2f} confidence")


def main():
    """Run all ML test generation examples."""
    print("🤖 WebPilot ML-Powered Test Generation")
    print("=" * 50)
    
    # Option 1: Record a real session (commented out for demo)
    # session_file = record_manual_session()
    # patterns = generate_tests_from_session(session_file)
    
    # Option 2: Demonstrate with sample data
    demonstrate_pattern_detection()
    demonstrate_test_prediction()
    
    # Option 3: Generate tests from a URL
    print("\n🌐 Generating Tests by Exploring Website")
    print("=" * 50)
    
    generator = IntelligentTestGenerator()
    print("\nExploring https://example.com...")
    tests = generator.generate_tests("https://example.com", depth=2)
    
    print(f"✅ Generated {len(tests)} test patterns")
    
    # Export generated tests
    output_dir = Path("auto_generated_tests")
    output_dir.mkdir(exist_ok=True)
    generator.export_tests(output_dir)
    
    # Generate report
    generate_test_report(generator)
    
    print("\n✨ ML test generation demonstration complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()