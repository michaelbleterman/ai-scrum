"""
Safety guardrails for sprint framework agents.
Implements content filtering, PII detection, and circuit breakers.
"""

import re
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter, deque


@dataclass
class GuardrailViolation:
    """Represents a guardrail policy violation"""
    severity: str  # 'warning', 'block'
    reason: str
    details: Dict[str, Any]


class PIIDetector:
    """Detects personally identifiable information in text"""
    
    # PII patterns
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        # Simple credit card regex (Luhn check not implemented here for speed)
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        # Generic API Key/Token patterns
        'api_key': r'\b(?:api[_-]?key|token|secret|password)["\s:=]+([A-Za-z0-9_\-]{20,})',
        'aws_key': r'\b(AKIA[0-9A-Z]{16})\b',
        'google_key': r'\b(AIza[0-9A-Za-z\\-_]{35})\b',
    }
    
    def detect(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect PII in text.
        
        Returns:
            List of (pii_type, matched_value) tuples
        """
        findings = []
        
        for pii_type, pattern in self.PATTERNS.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # re.findall returns tuple for groups, or str for partial match
                    # If multiple groups, we usually care about the capture group for value
                    value = match if isinstance(match, str) else match[0] if match else ""
                    if value:
                        findings.append((pii_type, value))
            except Exception:
                continue
        
        return findings
    
    def mask_pii(self, text: str) -> str:
        """
        Replace PII with masked placeholders.
        
        Example:
            "Email me at john@example.com" → "Email me at [EMAIL_REDACTED]"
        """
        masked = text
        
        for pii_type, pattern in self.PATTERNS.items():
            placeholder = f"[{pii_type.upper()}_REDACTED]"
            masked = re.sub(pattern, placeholder, masked, flags=re.IGNORECASE)
        
        return masked


class ContentFilter:
    """Filters harmful or disallowed content"""
    
    def __init__(self, denied_topics: Optional[List[str]] = None):
        """
        Args:
            denied_topics: List of topics agents should not discuss
        """
        self.denied_topics = denied_topics or [
            'credentials', 'passwords', 'tokens', 'secrets',
            'proprietary', 'confidential'
        ]
        
        # Harmful content keywords (basic implementation)
        # In production, use a classifier or more robust patterns
        self.harmful_keywords = [
            'rm -rf /', 
            'mkfs',
            ':(){ :|:& };:', # Fork bomb
            '> /dev/sda',    # Overwrite disk
            'format c:',
        ]
    
    def check_denied_topics(self, text: str) -> Optional[str]:
        """
        Check if text discusses denied topics.
        
        Returns:
            Violation reason if found, None otherwise
        """
        text_lower = text.lower()
        
        for topic in self.denied_topics:
            if topic.lower() in text_lower:
                return f"Denied topic detected: {topic}"
        
        return None
    
    def check_harmful_content(self, text: str) -> Optional[str]:
        """
        Check for potentially destructive commands.
        
        Returns:
            Violation reason if found, None otherwise
        """
        for keyword in self.harmful_keywords:
            if keyword in text:
                return f"Potentially harmful command detected: {keyword}"
        
        return None


class CircuitBreaker:
    """
    Prevents agents from repeating failed actions indefinitely.
    Tracks recent actions and blocks repetitive failures.
    """
    
    def __init__(self, window_size: int = 10, failure_threshold: int = 3):
        """
        Args:
            window_size: Number of recent actions to track
            failure_threshold: Max repeated failures before circuit opens
        """
        self.window_size = window_size
        self.failure_threshold = failure_threshold
        # Stores tuples of (action_hash, success_bool)
        self.recent_actions = deque(maxlen=window_size)
    
    def record_action(self, action: str, success: bool):
        """Record an action and its outcome"""
        # We hash the action (task description) to normalize
        # Using simple truncation/hash
        action_hash = hashlib.md5(action.encode('utf-8')).hexdigest()[:8]
        self.recent_actions.append((action_hash, success))
    
    def is_open(self, action: str) -> Tuple[bool, Optional[str]]:
        """
        Check if circuit is open for this action.
        
        Returns:
            (is_open, reason) tuple
        """
        action_hash = hashlib.md5(action.encode('utf-8')).hexdigest()[:8]
        
        # Count recent failures of this SPECIFIC action
        recent_failures = [
            1 for (ah, success) in self.recent_actions
            if ah == action_hash and not success
        ]
        
        failure_count = len(recent_failures)
        
        if failure_count >= self.failure_threshold:
            return True, f"Circuit open: action failed {failure_count} times in last {self.window_size} attempts"
        
        return False, None


class AgentGuardrails:
    """
    Main guardrail coordinator.
    Validates agent inputs and outputs against safety policies.
    """
    
    def __init__(
        self,
        denied_topics: Optional[List[str]] = None,
        enable_pii_detection: bool = True,
        enable_content_filter: bool = True,
        enable_circuit_breaker: bool = True
    ):
        self.pii_detector = PIIDetector() if enable_pii_detection else None
        self.content_filter = ContentFilter(denied_topics) if enable_content_filter else None
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
    
    def validate_input(self, user_input: str) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Validate user input before processing.
        
        Returns:
            (is_valid, violations) tuple
        """
        violations = []
        
        # Check for harmful content in inputs too
        if self.content_filter:
            harmful = self.content_filter.check_harmful_content(user_input)
            if harmful:
                violations.append(GuardrailViolation(
                    severity='block',
                    reason=harmful,
                    details={'type': 'harmful_content'}
                ))
        
        is_valid = not any(v.severity == 'block' for v in violations)
        return is_valid, violations
    
    def validate_output(
        self,
        agent_output: str,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[GuardrailViolation], str]:
        """
        Validate agent output before committing.
        
        Returns:
            (is_valid, violations, sanitized_output) tuple
        """
        violations = []
        sanitized = agent_output
        
        # PII Detection and masking
        if self.pii_detector:
            pii_findings = self.pii_detector.detect(agent_output)
            
            if pii_findings:
                violations.append(GuardrailViolation(
                    severity='block', # Can be 'warning' if we just mask
                    reason=f'PII detected: {len(pii_findings)} instances',
                    details={
                        'type': 'pii_exposure',
                        'pii_types': list(set([t for t, _ in pii_findings]))
                    }
                ))
                
                # Mask PII in output
                sanitized = self.pii_detector.mask_pii(agent_output)
        
        # Harmful content check
        if self.content_filter:
            harmful = self.content_filter.check_harmful_content(agent_output)
            if harmful:
                violations.append(GuardrailViolation(
                    severity='block',
                    reason=harmful,
                    details={'type': 'harmful_content'}
                ))
        
        # If we successfully sanitized (and only PII issues), we might allow it?
        # But if 'block' severity is used, we block.
        # Let's say PII is 'warning' if we can mask it?
        # For now, strict: if PII found, we flag it. But since we return sanitized, 
        # maybe we consider it 'valid' BUT returning sanitized version.
        # But violation list presence implies "something was wrong".
        # Let's assume validation fails if ANY block is present.
        
        is_valid = not any(v.severity == 'block' for v in violations)
        
        # If only PII and we sanitized, maybe we permit it?
        # Current logic: PII is marked 'block'. So it fails.
        # This forces the agent to retry without PII, which is safer than auto-sanitize in some cases,
        # but auto-sanitize is user-friendly. 
        # Let's change PII to 'warning' if we want auto-fix, but for now strict blocking is safer for "Agent Best Practices".
        
        return is_valid, violations, sanitized
    
    def check_circuit(self, action: str) -> Tuple[bool, Optional[str]]:
        """Check if circuit breaker allows this action"""
        if not self.circuit_breaker:
            return True, None
        
        is_open, reason = self.circuit_breaker.is_open(action)
        return not is_open, reason
    
    def record_action(self, action: str, success: bool):
        """Record action outcome for circuit breaker"""
        if self.circuit_breaker:
            self.circuit_breaker.record_action(action, success)


if __name__ == "__main__":
    # Test
    g = AgentGuardrails(enable_pii_detection=True)
    valid, viols, clean = g.validate_output("Call 555-123-4567")
    print(f"Valid: {valid}, Violations: {viols}, Clean: {clean}")
