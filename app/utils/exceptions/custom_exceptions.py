class ProductError(Exception):
    def __init__(self, message):
        self.message = message


class RequestPayloadError(Exception):
    def __init__(self, message):
        self.message = message
