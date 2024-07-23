from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import database
from passlib.context import CryptContext

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["argon2"])


@auth_router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Performs user authentication for API access.

    This endpoint accepts login credentials (username and password) via a POST request
    and returns an access token on successful authentication. If the credentials are
    incorrect or an error occurs, an HTTPException is raised with appropriate status
    code and details.

    **Raises:**

    - HTTPException:
        - 401 Unauthorized: If the username or password is incorrect.
        - 500 Internal Server Error: If an unexpected error occurs during authentication.

    **Returns:**

    A dictionary containing:

    - access_token: The generated JWT access token (if authentication is successful).
    - type: The token type (always "Bearer" in this implementation).

    """

    try:
        user = database.get_user(form_data.username)
        admin = database.get_admin(form_data.username)

        if user and pwd_context.verify(form_data.password, user["password"]):
            access_token = database.create_access_token(
                {"email": user["email"], "role": "user"}
            )
            return {"access_token": access_token, "type": "Bearer"}
        elif admin and pwd_context.verify(form_data.password, admin["password"]):
            access_token = database.create_access_token(
                {"email": admin["email"], "role": "admin"}
            )
            return {"access_token": access_token, "type": "Bearer"}
        else:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
