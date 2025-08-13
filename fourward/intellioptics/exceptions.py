class APIError(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        self.detail = response.text
        super().__init__(f"APIError {self.status_code}: {self.detail}")
