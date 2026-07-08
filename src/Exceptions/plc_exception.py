class PLCException(Exception):
    def __init__(self, message, errors:dict):
        super().__init__(message)
        self.errors = errors