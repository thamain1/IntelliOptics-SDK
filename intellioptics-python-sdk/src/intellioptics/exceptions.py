class IntelliOpticsError(Exception):
    pass

class AuthError(IntelliOpticsError):
    pass

class NotFound(IntelliOpticsError):
    pass

class ApiError(IntelliOpticsError):
    def __init__(self, status: int, message: str, payload=None):
        super().__init__(f"{status}: {message}")
        self.status = status
        self.payload = payload
