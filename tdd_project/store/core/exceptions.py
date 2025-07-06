class BaseException(Exception):
    message: str = "Internal Server Error"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message


class NotFoundException(BaseException):
    message: str = "Not Found"


class InsertionException(BaseException):
    message: str = "Error inserting product"
