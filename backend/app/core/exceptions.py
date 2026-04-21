from fastapi import HTTPException, status


class SlurmUnavailableError(Exception):
    pass


class SlurmCommandError(Exception):
    def __init__(self, message: str, returncode: int = -1):
        super().__init__(message)
        self.returncode = returncode


def slurm_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"message": "Slurm is unavailable", "code": "SLURM_UNAVAILABLE"},
    )


def not_found(resource: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"message": f"{resource} not found", "code": "NOT_FOUND"},
    )


def forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"message": "Insufficient permissions", "code": "FORBIDDEN"},
    )


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "Not authenticated", "code": "UNAUTHORIZED"},
        headers={"WWW-Authenticate": "Bearer"},
    )
