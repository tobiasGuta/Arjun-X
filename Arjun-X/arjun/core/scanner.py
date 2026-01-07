import re
from typing import List, Dict, Any, Union
from requests import Response
from arjun.core.requester import requester

class ParameterScorer:
    """
    Scores discovered parameters based on their name and behavior to estimate security risk.
    """
    def __init__(self) -> None:
        self.high_value_keywords: List[str] = ['id', 'user', 'admin', 'debug', 'file', 'path', 'redirect', 'url', 'cmd', 'exec']
        self.medium_value_keywords: List[str] = ['page', 'view', 'sort', 'order', 'key', 'token', 'auth']
        self.low_value_keywords: List[str] = ['utm', 'source', 'ref', '_']

    def score_parameter(self, param_name: str, reflection_found: bool = False, error_triggered: bool = False) -> int:
        """
        Calculate a risk score for a parameter.
        
        Args:
            param_name: The name of the parameter found.
            reflection_found: Whether the parameter payload was reflected in the response.
            error_triggered: Whether the parameter caused a server error.
            
        Returns:
            int: A score indicating potential risk (higher is riskier).
        """
        score = 10 # Base score for existing
        
        # Name Analysis
        lower_name = param_name.lower()
        if any(k in lower_name for k in self.high_value_keywords):
            score += 40
        elif any(k in lower_name for k in self.medium_value_keywords):
            score += 20
            
        # Behavior Analysis
        if reflection_found:
            score += 50 # High potential for XSS/SSTI
        if error_triggered:
            score += 30 # Potential for SQLi/RCE
            
        return score

    def get_risk_level(self, score: int) -> str:
        """
        Convert numeric score to a risk label.
        """
        if score >= 80: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 30: return "MEDIUM"
        return "LOW"

class AutoTester:
    """
    Conducts basic security checks on discovered parameters.
    """
    def __init__(self, request_template: Dict[str, Any]) -> None:
        self.request_template = request_template
        self.payloads: Dict[str, str] = {
            'reflection': 'ArjunTest<>"\'',
            'sqli': "'",
            'traversal': '../../../etc/passwd'
        }

    def test_parameter(self, param_name: str) -> List[str]:
        """
        Run basic tests (Reflection, SQLi error) on the parameter.
        """
        results: List[str] = []
        
        # Test 1: Reflection
        payload = {param_name: self.payloads['reflection']}
        resp = requester(self.request_template, payload)
        
        # requester returns str on error, or Response object
        if isinstance(resp, str): 
            # Request failed
            return results 
        
        if self.payloads['reflection'] in resp.text:
            results.append("Reflected Input (Potential XSS)")

        # Test 2: SQLi Error
        payload = {param_name: self.payloads['sqli']}
        resp = requester(self.request_template, payload)
        
        if isinstance(resp, str): 
            return results
        
        if "syntax error" in resp.text.lower() or "sql" in resp.text.lower():
            results.append("SQL Error Triggered")

        return results
