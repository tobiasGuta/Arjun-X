import re
from arjun.core.requester import requester

class ParameterScorer:
    def __init__(self):
        self.high_value_keywords = ['id', 'user', 'admin', 'debug', 'file', 'path', 'redirect', 'url', 'cmd', 'exec']
        self.medium_value_keywords = ['page', 'view', 'sort', 'order', 'key', 'token', 'auth']
        self.low_value_keywords = ['utm', 'source', 'ref', '_']

    def score_parameter(self, param_name, reflection_found=False, error_triggered=False):
        score = 10 # Base score for existing
        
        # Name Analysis
        if any(k in param_name.lower() for k in self.high_value_keywords):
            score += 40
        elif any(k in param_name.lower() for k in self.medium_value_keywords):
            score += 20
            
        # Behavior Analysis
        if reflection_found:
            score += 50 # High potential for XSS/SSTI
        if error_triggered:
            score += 30 # Potential for SQLi/RCE
            
        return score

    def get_risk_level(self, score):
        if score >= 80: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 30: return "MEDIUM"
        return "LOW"

class AutoTester:
    def __init__(self, request_template):
        self.request_template = request_template
        self.payloads = {
            'reflection': 'ArjunTest<>"\'',
            'sqli': "'",
            'traversal': '../../../etc/passwd'
        }

    def test_parameter(self, param_name):
        results = []
        
        # Test 1: Reflection
        payload = {param_name: self.payloads['reflection']}
        resp = requester(self.request_template, payload)
        
        # requester returns str on error, or Response object
        if isinstance(resp, str): 
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
