#!/usr/bin/env python3
"""
WebPilot ML-Based Test Generation
Uses machine learning to automatically generate test cases from user interactions
"""

import json
import pickle
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from ..core import ActionType, WebPilotSession


@dataclass
class UserAction:
    """Represents a user action for ML analysis"""
    action_type: ActionType
    selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    success: bool = True
    page_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_vector(self) -> List[float]:
        """Convert action to numerical vector for ML"""
        vector = [
            float(self.action_type.value),
            len(self.selector or ''),
            len(self.url or ''),
            len(self.text or ''),
            self.duration_ms,
            float(self.success),
            len(self.page_state)
        ]
        return vector


@dataclass
class TestPattern:
    """Represents a discovered test pattern"""
    name: str
    actions: List[UserAction]
    frequency: int = 1
    confidence: float = 0.0
    category: str = "general"
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    
    def to_test_code(self, language: str = "python") -> str:
        """Generate test code from pattern"""
        if language == "python":
            return self._generate_python_test()
        elif language == "javascript":
            return self._generate_javascript_test()
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_python_test(self) -> str:
        """Generate Python test code"""
        code = f'''def test_{self.name.lower().replace(" ", "_")}(pilot):
    """Auto-generated test: {self.name}"""
    
    # Preconditions
'''
        for pre in self.preconditions:
            code += f"    # {pre}\n"
        
        code += "\n    # Test actions\n"
        
        for action in self.actions:
            if action.action_type == ActionType.NAVIGATE:
                code += f"    result = pilot.navigate('{action.url}')\n"
            elif action.action_type == ActionType.CLICK:
                if action.selector:
                    code += f"    result = pilot.click(selector='{action.selector}')\n"
                elif action.text:
                    code += f"    result = pilot.click(text='{action.text}')\n"
            elif action.action_type == ActionType.TYPE:
                code += f"    result = pilot.type_text('{action.text}', selector='{action.selector}')\n"
            elif action.action_type == ActionType.SCREENSHOT:
                code += f"    result = pilot.screenshot('test_screenshot.png')\n"
            elif action.action_type == ActionType.WAIT:
                code += f"    result = pilot.wait_for_element('{action.selector}')\n"
            
            code += "    assert result.success\n\n"
        
        # Postconditions
        if self.postconditions:
            code += "    # Postconditions\n"
            for post in self.postconditions:
                code += f"    # {post}\n"
        
        return code
    
    def _generate_javascript_test(self) -> str:
        """Generate JavaScript test code"""
        code = f'''describe('{self.name}', () => {{
    it('should complete the user flow', async () => {{
        // Preconditions
'''
        for pre in self.preconditions:
            code += f"        // {pre}\n"
        
        code += "\n        // Test actions\n"
        
        for action in self.actions:
            if action.action_type == ActionType.NAVIGATE:
                code += f"        await pilot.navigate('{action.url}');\n"
            elif action.action_type == ActionType.CLICK:
                if action.selector:
                    code += f"        await pilot.click('{action.selector}');\n"
                elif action.text:
                    code += f"        await pilot.clickText('{action.text}');\n"
            elif action.action_type == ActionType.TYPE:
                code += f"        await pilot.type('{action.selector}', '{action.text}');\n"
            elif action.action_type == ActionType.SCREENSHOT:
                code += f"        await pilot.screenshot('test_screenshot.png');\n"
            elif action.action_type == ActionType.WAIT:
                code += f"        await pilot.waitForElement('{action.selector}');\n"
        
        # Postconditions
        if self.postconditions:
            code += "\n        // Postconditions\n"
            for post in self.postconditions:
                code += f"        // {post}\n"
        
        code += "    });\n});"
        return code


class PatternDetector:
    """Detects patterns in user interactions using ML"""
    
    def __init__(self, min_pattern_length: int = 3, min_frequency: int = 2):
        self.min_pattern_length = min_pattern_length
        self.min_frequency = min_frequency
        self.patterns: List[TestPattern] = []
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.scaler = StandardScaler()
        self.logger = logging.getLogger('PatternDetector')
        
    def detect_patterns(self, actions: List[UserAction]) -> List[TestPattern]:
        """Detect repeating patterns in user actions"""
        patterns = []
        
        # Convert actions to sequences
        sequences = self._extract_sequences(actions)
        
        # Find frequent patterns
        frequent_patterns = self._find_frequent_patterns(sequences)
        
        # Cluster similar patterns
        clustered_patterns = self._cluster_patterns(frequent_patterns)
        
        # Generate test patterns
        for cluster in clustered_patterns:
            pattern = self._create_test_pattern(cluster)
            patterns.append(pattern)
        
        self.patterns = patterns
        return patterns
    
    def _extract_sequences(self, actions: List[UserAction], 
                          window_size: int = 10) -> List[List[UserAction]]:
        """Extract action sequences using sliding window"""
        sequences = []
        
        for i in range(len(actions) - window_size + 1):
            sequence = actions[i:i + window_size]
            sequences.append(sequence)
        
        return sequences
    
    def _find_frequent_patterns(self, sequences: List[List[UserAction]]) -> List[List[UserAction]]:
        """Find frequently occurring patterns"""
        # Create hash for each sequence
        sequence_hashes = defaultdict(list)
        
        for seq in sequences:
            # Create hash from action types and selectors
            seq_str = '|'.join([
                f"{a.action_type.value}:{a.selector or ''}" 
                for a in seq[:self.min_pattern_length]
            ])
            seq_hash = hashlib.md5(seq_str.encode()).hexdigest()
            sequence_hashes[seq_hash].append(seq)
        
        # Filter by minimum frequency
        frequent = []
        for hash_val, seqs in sequence_hashes.items():
            if len(seqs) >= self.min_frequency:
                frequent.extend(seqs[:1])  # Take one representative
        
        return frequent
    
    def _cluster_patterns(self, patterns: List[List[UserAction]]) -> List[List[List[UserAction]]]:
        """Cluster similar patterns together"""
        if not patterns:
            return []
        
        # Convert patterns to vectors
        vectors = []
        for pattern in patterns:
            pattern_vector = []
            for action in pattern[:self.min_pattern_length]:
                pattern_vector.extend(action.to_vector())
            vectors.append(pattern_vector)
        
        # Pad vectors to same length
        max_len = max(len(v) for v in vectors)
        vectors = [v + [0] * (max_len - len(v)) for v in vectors]
        
        # Scale features
        X = np.array(vectors)
        X_scaled = self.scaler.fit_transform(X)
        
        # Cluster using DBSCAN
        clustering = DBSCAN(eps=0.3, min_samples=2)
        labels = clustering.fit_predict(X_scaled)
        
        # Group patterns by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[label].append(patterns[i])
        
        return list(clusters.values())
    
    def _create_test_pattern(self, cluster: List[List[UserAction]]) -> TestPattern:
        """Create a test pattern from a cluster of similar sequences"""
        # Use the most common sequence as representative
        representative = cluster[0]
        
        # Generate pattern name
        action_types = [a.action_type.name for a in representative[:3]]
        name = f"Pattern_{'-'.join(action_types)}"
        
        # Analyze preconditions (first action usually navigation)
        preconditions = []
        if representative[0].action_type == ActionType.NAVIGATE:
            preconditions.append(f"Navigate to {representative[0].url}")
        
        # Analyze postconditions (check final state)
        postconditions = []
        if representative[-1].success:
            postconditions.append("Verify successful completion")
        
        return TestPattern(
            name=name,
            actions=representative,
            frequency=len(cluster),
            confidence=len(cluster) / 10.0,  # Simple confidence score
            preconditions=preconditions,
            postconditions=postconditions
        )


class TestPredictor:
    """Predicts next likely test actions using ML"""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or Path("webpilot_ml_model.pkl")
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.action_history: List[UserAction] = []
        self.is_trained = False
        self.logger = logging.getLogger('TestPredictor')
        
        # Load model if exists
        if self.model_path.exists():
            self.load_model()
    
    def train(self, training_data: List[Tuple[List[UserAction], UserAction]]):
        """
        Train the predictor on action sequences
        
        Args:
            training_data: List of (context_actions, next_action) tuples
        """
        if not training_data:
            self.logger.warning("No training data provided")
            return
        
        # Prepare features and labels
        X = []
        y = []
        
        for context, next_action in training_data:
            # Create feature vector from context
            features = self._extract_features(context)
            X.append(features)
            
            # Label is the next action type
            y.append(next_action.action_type.value)
        
        # Train classifier
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        score = self.classifier.score(X_test, y_test)
        self.logger.info(f"Model trained with accuracy: {score:.2f}")
        
        self.is_trained = True
        self.save_model()
    
    def predict_next_action(self, context: List[UserAction]) -> Tuple[ActionType, float]:
        """
        Predict the next likely action
        
        Returns:
            Tuple of (predicted_action_type, confidence)
        """
        if not self.is_trained:
            self.logger.warning("Model not trained yet")
            return ActionType.NAVIGATE, 0.0
        
        features = self._extract_features(context)
        
        # Predict with probability
        prediction = self.classifier.predict([features])[0]
        probabilities = self.classifier.predict_proba([features])[0]
        confidence = max(probabilities)
        
        return ActionType(prediction), confidence
    
    def suggest_test_completion(self, partial_test: List[UserAction], 
                               max_steps: int = 5) -> List[UserAction]:
        """Suggest actions to complete a test"""
        if not self.is_trained:
            return []
        
        suggested = []
        context = partial_test.copy()
        
        for _ in range(max_steps):
            action_type, confidence = self.predict_next_action(context)
            
            if confidence < 0.3:  # Low confidence, stop suggesting
                break
            
            # Create suggested action
            suggested_action = UserAction(
                action_type=action_type,
                selector="[suggested-selector]",
                text="[suggested-text]" if action_type == ActionType.TYPE else None
            )
            
            suggested.append(suggested_action)
            context.append(suggested_action)
        
        return suggested
    
    def _extract_features(self, actions: List[UserAction]) -> List[float]:
        """Extract features from action sequence"""
        if not actions:
            return [0] * 20  # Return zero vector
        
        features = []
        
        # Last N action types
        last_n = 5
        for i in range(last_n):
            if i < len(actions):
                features.append(float(actions[-(i+1)].action_type.value))
            else:
                features.append(0)
        
        # Action type distribution
        action_counts = Counter(a.action_type.value for a in actions)
        for action_type in ActionType:
            features.append(action_counts.get(action_type.value, 0))
        
        # Timing features
        if len(actions) > 1:
            durations = [a.duration_ms for a in actions]
            features.extend([
                np.mean(durations),
                np.std(durations),
                np.min(durations),
                np.max(durations)
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Success rate
        success_rate = sum(a.success for a in actions) / len(actions)
        features.append(success_rate)
        
        return features
    
    def save_model(self):
        """Save trained model to disk"""
        if self.is_trained:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.classifier, f)
            self.logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load model from disk"""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.classifier = pickle.load(f)
            self.is_trained = True
            self.logger.info(f"Model loaded from {self.model_path}")


class IntelligentTestGenerator:
    """Main class for ML-based test generation"""
    
    def __init__(self, session: Optional[WebPilotSession] = None):
        self.session = session or WebPilotSession()
        self.pattern_detector = PatternDetector()
        self.test_predictor = TestPredictor()
        self.generated_tests: List[TestPattern] = []
        self.logger = logging.getLogger('IntelligentTestGenerator')
    
    def learn_from_session(self, session_file: Path) -> List[TestPattern]:
        """Learn patterns from a recorded session"""
        # Load session data
        session = WebPilotSession.load(session_file)
        
        # Convert to UserActions
        actions = self._convert_session_to_actions(session)
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(actions)
        
        # Train predictor
        training_data = self._create_training_data(actions)
        self.test_predictor.train(training_data)
        
        self.generated_tests = patterns
        return patterns
    
    def generate_tests(self, url: str, depth: int = 3) -> List[TestPattern]:
        """Generate tests by exploring a website"""
        from ..core import WebPilot
        
        tests = []
        
        with WebPilot() as pilot:
            # Start at URL
            pilot.start(url)
            
            # Explore and generate tests
            self._explore_and_generate(pilot, depth, tests)
        
        self.generated_tests = tests
        return tests
    
    def _explore_and_generate(self, pilot, depth: int, tests: List[TestPattern], 
                             visited: set = None):
        """Recursively explore and generate tests"""
        if visited is None:
            visited = set()
        
        if depth <= 0:
            return
        
        current_url = pilot.driver.current_url if pilot.driver else ""
        
        if current_url in visited:
            return
        
        visited.add(current_url)
        
        # Find interactive elements
        elements = pilot.find_elements("a, button, input, select")
        
        for element in elements[:10]:  # Limit exploration
            # Create test for interacting with element
            actions = [
                UserAction(ActionType.NAVIGATE, url=current_url),
                UserAction(ActionType.CLICK, selector=element.get('selector'))
            ]
            
            # Predict likely next actions
            if self.test_predictor.is_trained:
                suggested = self.test_predictor.suggest_test_completion(actions, max_steps=3)
                actions.extend(suggested)
            
            # Create test pattern
            pattern = TestPattern(
                name=f"Test_{element.get('tag')}_{len(tests)}",
                actions=actions,
                category="exploration"
            )
            
            tests.append(pattern)
            
            # Recursively explore (limited)
            if element.get('tag') == 'a' and depth > 1:
                pilot.click(selector=element.get('selector'))
                self._explore_and_generate(pilot, depth - 1, tests, visited)
                pilot.back()
    
    def _convert_session_to_actions(self, session: WebPilotSession) -> List[UserAction]:
        """Convert session history to UserActions"""
        actions = []
        
        for action_result in session.history:
            action = UserAction(
                action_type=action_result.action_type,
                selector=action_result.data.get('selector'),
                url=action_result.data.get('url'),
                text=action_result.data.get('text'),
                duration_ms=action_result.duration_ms,
                success=action_result.success
            )
            actions.append(action)
        
        return actions
    
    def _create_training_data(self, actions: List[UserAction]) -> List[Tuple[List[UserAction], UserAction]]:
        """Create training data for predictor"""
        training_data = []
        
        context_size = 5
        for i in range(context_size, len(actions)):
            context = actions[i-context_size:i]
            next_action = actions[i]
            training_data.append((context, next_action))
        
        return training_data
    
    def export_tests(self, output_dir: Path, language: str = "python"):
        """Export generated tests to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, pattern in enumerate(self.generated_tests):
            # Generate test code
            code = pattern.to_test_code(language)
            
            # Write to file
            if language == "python":
                filename = f"test_{pattern.name.lower()}.py"
            else:
                filename = f"test_{pattern.name.lower()}.js"
            
            filepath = output_dir / filename
            filepath.write_text(code)
            
            self.logger.info(f"Exported test to {filepath}")
    
    def generate_test_report(self) -> Dict:
        """Generate report of discovered patterns and tests"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_patterns': len(self.generated_tests),
            'categories': defaultdict(int),
            'confidence_distribution': [],
            'patterns': []
        }
        
        for pattern in self.generated_tests:
            report['categories'][pattern.category] += 1
            report['confidence_distribution'].append(pattern.confidence)
            
            report['patterns'].append({
                'name': pattern.name,
                'frequency': pattern.frequency,
                'confidence': pattern.confidence,
                'num_actions': len(pattern.actions),
                'category': pattern.category
            })
        
        return report


def test_ml_generation():
    """Test ML-based test generation"""
    print("🤖 Testing ML-Based Test Generation")
    print("=" * 50)
    
    # Create sample actions
    sample_actions = [
        UserAction(ActionType.NAVIGATE, url="https://example.com"),
        UserAction(ActionType.CLICK, selector="#login"),
        UserAction(ActionType.TYPE, selector="#username", text="testuser"),
        UserAction(ActionType.TYPE, selector="#password", text="testpass"),
        UserAction(ActionType.CLICK, selector="#submit"),
        UserAction(ActionType.WAIT, selector=".dashboard"),
        
        # Repeat pattern
        UserAction(ActionType.NAVIGATE, url="https://example.com"),
        UserAction(ActionType.CLICK, selector="#login"),
        UserAction(ActionType.TYPE, selector="#username", text="admin"),
        UserAction(ActionType.TYPE, selector="#password", text="admin123"),
        UserAction(ActionType.CLICK, selector="#submit"),
        UserAction(ActionType.WAIT, selector=".dashboard"),
    ]
    
    # Test pattern detection
    print("\n1. Pattern Detection")
    detector = PatternDetector(min_pattern_length=3, min_frequency=1)
    patterns = detector.detect_patterns(sample_actions)
    
    print(f"   Found {len(patterns)} patterns")
    for pattern in patterns:
        print(f"   - {pattern.name}: {len(pattern.actions)} actions, frequency={pattern.frequency}")
    
    # Test code generation
    print("\n2. Test Code Generation")
    if patterns:
        pattern = patterns[0]
        
        # Generate Python test
        python_code = pattern.to_test_code("python")
        print("\n   Python Test:")
        print("   " + "\n   ".join(python_code.split("\n")[:10]))
        
        # Generate JavaScript test
        js_code = pattern.to_test_code("javascript")
        print("\n   JavaScript Test:")
        print("   " + "\n   ".join(js_code.split("\n")[:10]))
    
    # Test prediction
    print("\n3. Action Prediction")
    predictor = TestPredictor()
    
    # Create training data
    training_data = []
    for i in range(5, len(sample_actions)):
        context = sample_actions[i-5:i]
        next_action = sample_actions[i]
        training_data.append((context, next_action))
    
    predictor.train(training_data)
    
    # Make prediction
    test_context = sample_actions[:3]
    predicted_action, confidence = predictor.predict_next_action(test_context)
    print(f"   Predicted next action: {predicted_action.name} (confidence: {confidence:.2f})")
    
    # Test completion suggestion
    suggested = predictor.suggest_test_completion(test_context, max_steps=3)
    print(f"   Suggested {len(suggested)} actions to complete test")
    
    print("\n✨ ML test generation complete!")


if __name__ == "__main__":
    test_ml_generation()