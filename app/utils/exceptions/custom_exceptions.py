class ProductError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class RequestPayloadError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
