from fastapi import APIRouter, Depends, HTTPException
from model import User
import database

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.post("/add")
def add_user(new_user: User):
    """
    This API endpoint allows users to register a new account.

    Args:
        new_user (User): The user data to be added. (Expected data format as per the User model)

    Returns:
        dict: A dictionary containing a success message upon successful user registration,
               including the newly generated username and ID, or a message indicating an existing user with the same email.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        new_user.generate_id()
        new_user.hash_password()
        exist = user_col.find_one({"email": new_user.email}, {"_id": 0})
        if exist:
            return {"message": f"User with email id {new_user.email} already exist"}
        else:
            user_col.insert_one(new_user.dict())

        added_user = user_col.find_one({"email": new_user.email}, {"_id": 0})
        if added_user:
            return {
                "message": f"User added with Username : {added_user["username"]} and User ID : {added_user["id"]}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.get("/show/all")
def show_all_user(page_no: int = 1, page_size: int = 50):
    """
    This API endpoint retrieves a paginated list of all users in the database, excluding password information.

    Args:
        page_no (int, optional): The current page number (defaults to 1).
        page_size (int, optional): The number of users to retrieve per page (defaults to 50).

    Returns:
        dict: A dictionary containing information about the retrieved users, including:
            * Page_No (int): The current page number.
            * Page_Size (int): The number of users retrieved per page.
            * Total (int): The total number of users in the database.
            * Users (list): A list of user data (excluding password) as per the User model for the current page.
            * message (str, optional): A message indicating no users were found if applicable.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        skip_size = (page_no - 1) * page_size
        total_user = user_col.count_documents({})
        result = (
            user_col.find({}, {"_id": 0, "password": 0})
            .skip(skip_size)
            .limit(page_size)
        )
        result = list(result)

        response = {
            "Page_No": page_no,
            "Page_Size": page_size,
            "Total": total_user,
            "Users": result,
        }
        if len(result) == 0:
            return {"Message": "No More Users Left in the User Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.get("/show/{email}")
def show_user(email: str):
    """
    This API endpoint retrieves details of a specific user by their email address, excluding password information.

    Args:
        email (str): The email address of the user to retrieve.

    Returns:
        dict: A dictionary containing the user data (excluding password) as per the User model if found,
               or a message indicating the user was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        exist = user_col.find_one({"email": email}, {"_id": 0, "password": 0})
        if not exist:
            return f"User with user email {email} does not exist"
        else:
            return exist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.put("/update/address/{email}")
def update_user_address(
    email: str, address: str, current_user=Depends(database.get_current_user)
):
    """
    This API endpoint allows authorized users to update their address by providing their email address.

    Args:
        email (str): The email address of the user to update.
        address (str): The new address for the user.
        current_user (User, optional): The currently logged-in user (for authorization). Depends on get_current_user dependency.

    Returns:
        dict: A dictionary containing the updated user data (excluding password) as per the User model if successful,
               or a message indicating the user was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        exist = user_col.find_one({"email": email})
        if exist:
            user_col.update_one({"email": email}, {"$set": {"address": address}})
            return user_col.find_one({"email": email}, {"_id": 0})
        else:
            return f"Product with email : {email} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.delete("/delete/self")
def delete_your_account(current_user=Depends(database.get_current_user)):
    """
    API endpoint to delete the currently logged-in user's account.

    Args:
        current_user (schemas.User): The currently logged-in user (for authorization). Depends on get_current_user dependency.

    Returns:
        dict: A dictionary containing a success message upon successful user deletion,
               or a message indicating the user was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        email = current_user["email"]
        exist = user_col.find_one({"email": email}, {"_id": 0, "password": 0})
        if not exist:
            return f"User with user email {email} does not exist"
        else:
            user_col.delete_one({"email": email})
            return f"User with email : {email} is deleted from the record"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
