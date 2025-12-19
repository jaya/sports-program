from typing import Any

class BusinessException(Exception):
    pass


class EntityNotFoundError(BusinessException):
    def __init__(self, entity: str, identifier: Any):
        self.message = f"{entity} with identifier {identifier} not found."
        super().__init__(self.message)


class DuplicateEntityError(BusinessException):
    def __init__(self, entity: str, field: str, value: Any):
        self.message = f"{entity} with {field} '{value}' already exists."
        super().__init__(self.message)


class BusinessRuleViolationError(BusinessException):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, message: str = "An unexpected error occurred while processing your request."):
        self.message = message
        super().__init__(self.message)
