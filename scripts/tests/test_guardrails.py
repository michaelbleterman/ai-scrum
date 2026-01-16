import unittest
import sys
import os

# Add scripts dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint_guardrails import (
    PIIDetector, ContentFilter, CircuitBreaker, AgentGuardrails
)


class TestPIIDetector(unittest.TestCase):
    
    def setUp(self):
        self.detector = PIIDetector()
    
    def test_email_detection(self):
        text = "Contact: john@example.com"
        findings = self.detector.detect(text)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][0], 'email')
        self.assertEqual(findings[0][1], 'john@example.com')
    
    def test_api_key_detection(self):
        # Using a fake key structure to avoid triggering real secret scanners safely
        text = 'API_KEY="AIzaSyA_FakeKeyForTesting1234567890ABCD"'
        findings = self.detector.detect(text)
        
        self.assertTrue(any(t == 'google_key' or t == 'api_key' for t, _ in findings))
    
    def test_masking(self):
        text = "My email is test@domain.com and phone is 555-123-4567"
        masked = self.detector.mask_pii(text)
        
        self.assertNotIn("test@domain.com", masked)
        self.assertNotIn("555-123-4567", masked)
        self.assertIn("[EMAIL_REDACTED]", masked)
        self.assertIn("[PHONE_REDACTED]", masked)


class TestContentFilter(unittest.TestCase):
    
    def setUp(self):
        self.filter = ContentFilter(denied_topics=['password', 'secret'])
    
    def test_denied_topic(self):
        text = "Please provide your password"
        violation = self.filter.check_denied_topics(text)
        
        self.assertIsNotNone(violation)
        self.assertIn("password", violation.lower())
    
    def test_harmful_command(self):
        text = "Run: rm -rf / --no-preserve-root"
        violation = self.filter.check_harmful_content(text)
        
        self.assertIsNotNone(violation)
        self.assertIn("harmful", violation.lower())


class TestCircuitBreaker(unittest.TestCase):
    
    def setUp(self):
        self.breaker = CircuitBreaker(window_size=5, failure_threshold=3)
    
    def test_circuit_opens_after_threshold(self):
        action = "npm install broken-package"
        
        # Record 3 failures
        for _ in range(3):
            self.breaker.record_action(action, success=False)
        
        # Circuit should be open
        is_open, reason = self.breaker.is_open(action)
        self.assertTrue(is_open)
        self.assertIn("failed 3 times", reason)
    
    def test_circuit_stays_closed_on_success(self):
        action = "npm install valid-package"
        
        # Record mixed outcomes
        self.breaker.record_action(action, success=False)
        self.breaker.record_action(action, success=True)
        self.breaker.record_action(action, success=False)
        
        # Circuit should stay closed (< 3 failures)
        is_open, reason = self.breaker.is_open(action)
        self.assertFalse(is_open)

if __name__ == '__main__':
    unittest.main()
