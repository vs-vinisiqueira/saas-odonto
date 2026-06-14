from fastapi import HTTPException, status


class NotFound(HTTPException):
    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class Unauthorized(HTTPException):
    def __init__(self, detail: str = "Não autorizado"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class Forbidden(HTTPException):
    def __init__(self, detail: str = "Permissão insuficiente"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class Conflict(HTTPException):
    def __init__(self, detail: str = "Conflito de estado"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
