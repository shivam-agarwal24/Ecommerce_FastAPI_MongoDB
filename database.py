from pymongo import MongoClient
from os import getenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from model import TokenData
from typing import Optional
from passlib.context import CryptContext


def connect_to_mongo():
    """
    Connects to MongoDB using the URL provided in environment variables.

    Returns:
        MongoClient: Connected MongoDB client instance.
    """
    client = MongoClient(getenv("Mongo_URL"))
    return client.ECommerce


def get_product_collection(db):
    """Retrieves the 'Product' collection from the provided database."""
    return db.Product


def get_user_collection(db):
    """Retrieves the 'User' collection from the provided database."""
    return db.User


def get_order_collection(db):
    """Retrieves the 'Order' collection from the provided database."""
    return db.Order


def get_admin_collection(db):
    """Retrieves the 'Admin' collection from the provided database."""
    return db.Admin


def get_cart_collection(db):
    """Retrieves the 'Cart' collection from the provided database."""
    return db.Cart


outh2_scheme = OAuth2PasswordBearer("/auth/token")
"""
An instance of OAuth2PasswordBearer for authentication using JWT tokens.

The tokenUrl argument specifies the endpoint for obtaining access tokens.
"""


SECRET_KEY: str = str(getenv("Secret_Key"))
ALGO = "HS256"
EXPIRATION_DURATION = 60


def get_user(email: str):
    """
    Retrieves a user from the database by email address.

    Args:
        email (str): The email address of the user to retrieve.

    Returns:
        dict or None: A dictionary containing user data if found, otherwise None.
    """
    db = connect_to_mongo()
    user_col = get_user_collection(db)
    user = user_col.find_one({"email": email})
    return user


def get_admin(email: str):
    """
    Retrieves an administrator from the database by email address.

    Args:
        email (str): The email address of the administrator to retrieve.

    Returns:
        dict or None: A dictionary containing admin data if found, otherwise None.
    """
    db = connect_to_mongo()
    admin_col = get_admin_collection(db)
    admin = admin_col.find_one({"email": email})
    return admin


def create_access_token(data: dict, expiriration: Optional[timedelta] = None):
    """
    Creates an access token using JWT.

    Args:
        data (dict): The data to include in the token.
        expiration (Optional[timedelta], optional): The expiration time for the token.
            Defaults to EXPIRATION_DURATION if not provided.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expiriration:
        expires = datetime.utcnow() + expiriration
    else:
        expires = datetime.utcnow() + timedelta(minutes=EXPIRATION_DURATION)

    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGO)
    return encoded_jwt


def get_current_user(token: str = Depends(outh2_scheme)):
    """
    Retrieves the current user (user or admin) based on the provided access token.

    This function performs the following steps:

    1. **Dependency Injection:** Leverages the `Depends` dependency injection mechanism
       from FastAPI to retrieve the access token from the request headers using the
       configured `outh2_scheme` (usually set to "/auth/token").

    2. **Error Handling:** Defines a custom `HTTPException` to handle various authentication
       errors with a 401 (Unauthorized) status code and appropriate details.

    3. **Token Decoding:** Attempts to decode the provided access token using the JWT library.
       - If the token is invalid (e.g., expired, malformed, or incorrect signature), a
         `JWTError` exception is raised.
       - If decoding is successful, the payload (decoded data) is extracted as a dictionary.

    4. **Payload Validation:** Checks for the presence of essential fields in the payload:
       - `"email"`: The email address associated with the user or admin.
       - `"role"`: The role of the user ("user" or "admin").
       - If either field is missing, the `credentials_exception` is raised.

    5. **User/Admin Retrieval:** Based on the extracted role:
       - If the role is `"user"`, fetches the user data from the database using the `get_user`
         function.
       - If the role is `"admin"`, fetches the admin data from the database using the
         `get_admin` function.
       - If the user or admin cannot be found in the database, the `credentials_exception`
         is raised.

    6. **Return User/Admin Data:** If all validations and retrievals are successful, returns
       the dictionary containing user or admin data, respectively.

    Raises:
        HTTPException: If the token is invalid, credentials are invalid
                       (missing email or role in payload, or user/admin not found),
                       or an unexpected error occurs.

    Returns:
        dict: A dictionary containing the user data (if user role) or admin data (if admin role)
              if authentication is successful, otherwise raises an exception.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        email: str = payload["email"]
        role: str = payload["role"]
        if email is None or role is None:
            raise credentials_exception
        else:
            token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    if token_data.role == "user":
        user = get_user(token_data.email)
        if user is None:
            raise credentials_exception
        return user
    elif token_data.role == "admin":
        admin = get_admin(token_data.email)
        if admin is None:
            raise credentials_exception
        return admin
    else:
        raise credentials_exception


def get_current_admin(current_user: dict = Depends(get_current_user)):
    """
    Ensures the current user is an administrator and returns their data.

    This function depends on the `get_current_user` function to retrieve the
    currently authenticated user (user or admin). It then performs the following:

    1. **Admin Role Check:** Verifies if the `"is_admin"` key exists in the `current_user`
       dictionary and its value is `True`. If not, it raises an `HTTPException` with a 403
       (Forbidden) status code indicating unauthorized access.

    2. **Return Admin Data:** If the user is an admin, simply returns the `current_user`
       dictionary containing their data.

    Raises:
        HTTPException: If the user is not an administrator (forbidden access).

    Returns:
        dict: The dictionary containing admin data if the user is an admin,
              otherwise raises an exception.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden! You are not authorized to access this API",
        )
    return current_user


def authenticate_user(db, email: str, password: str):
    """
    Authenticates a user based on email and password.

    Args:
        db (MongoClient): MongoDB client instance.
        email (str): Email address of the user.
        password (str): Password of the user.

    Returns:
        dict or bool: User document from MongoDB if authentication succeeds,
                      False if user not found or authentication fails.
    """
    user = get_user(email)
    if not user:
        return False
    pswd_context = CryptContext(schemes=["argon2"])
    if not pswd_context.verify(password, user["password"]):
        return False
    return user


def authenticate_admin(db, email: str, password: str):
    """
    Authenticates an admin based on email and password.

    Args:
        db (MongoClient): MongoDB client instance.
        email (str): Email address of the admin.
        password (str): Password of the admin.

    Returns:
        dict or bool: Admin document from MongoDB if authentication succeeds,
                      False if admin not found or authentication fails.
    """
    admin = get_admin(email)
    if not admin:
        return False
    pswd_context = CryptContext(schemes=["argon2"])
    if not pswd_context.verify(password, admin["password"]):
        return False
    return admin
