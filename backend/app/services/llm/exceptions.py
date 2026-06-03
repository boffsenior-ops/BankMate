class LLMError(Exception):
    pass

class LLMRateLimitError(LLMError):
    """Raised on 429 Rate Limit responses"""
    pass

class LLMAuthError(LLMError):
    """Raised on 401/403 Authentication or Authorization errors"""
    pass

class LLMQuotaError(LLMError):
    """Raised on insufficient quota errors (e.g., OpenAI 'insufficient_quota')"""
    pass

class LLMConnectionError(LLMError):
    """Raised on network or DNS connection errors"""
    pass

class LLMTimeoutError(LLMError):
    """Raised on request timeout"""
    pass

class LLMServerError(LLMError):
    """Raised on 5xx Server errors"""
    pass
