from fastapi import APIRouter, Depends, HTTPException
from model import Admin
import database

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.post("/add")
def add_admin(new_admin: Admin):
    """
    Adds a new admin user to the database.

    **Request Body:**

    - **Admin (model):** An object representing the new admin user with required fields
      (likely including username, email, password etc. as defined in the `Admin` model).

    **Response:**

    - **201 Created:** If the admin user is successfully added, the response includes
      the newly created admin object (excluding password for security reasons).
    - **400 Bad Request:** If an admin with the same email already exists.
    - **500 Internal Server Error:** If an unexpected error occurs.

    **Raises:**

    - `HTTPException`: If an unexpected error occurs during database operations.
    """
    try:
        db = database.connect_to_mongo()
        admin_col = database.get_admin_collection(db)
        new_admin.generate_id()
        new_admin.hash_password()
        exist = admin_col.find_one({"email": new_admin.email}, {"_id": 0})
        if exist:
            return f"User with email id {new_admin.email} already exist"
        else:
            admin_col.insert_one(new_admin.dict())

        added_user = admin_col.find_one({"email": new_admin.email}, {"_id": 0})
        if added_user:
            return f"User added with Username : {added_user["username"]} and User ID : {added_user["id"]}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/show/all")
def show_all_admin(page_no: int = 1, page_size: int = 50):
    """
    Retrieves a paginated list of all admin users from the database.

    **Query Parameters:**

    - **page_no (int, optional):** The current page number (defaults to 1).
    - **page_size (int, optional):** The number of admin users per page (defaults to 50).

    **Response:**

    - **200 OK:** A dictionary containing pagination information (`Page_No`, `Page_Size`,
      `Total`), and a list of admin user objects (excluding password for security reasons).
    - **404 Not Found:** If there are no admin users in the collection.
    - **500 Internal Server Error:** If an unexpected error occurs.

    **Raises:**

    - `HTTPException`: If an unexpected error occurs during database operations.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_admin_collection(db)
        skip_size = (page_no - 1) * page_size
        total_admin = user_col.count_documents({})
        result = (
            user_col.find({}, {"_id": 0, "password": 0})
            .skip(skip_size)
            .limit(page_size)
        )
        result = list(result)

        response = {
            "Page_No": page_no,
            "Page_Size": page_size,
            "Total": total_admin,
            "Admin Users": result,
        }
        if len(result) == 0:
            return {"Message": "No More Admins Left in the Admin Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/show/{email}")
def show_admin(email: str):
    """
    Retrieves an admin user by their email address.

    **Path Parameter:**

    - **email (str):** The email address of the admin user to retrieve.

    **Response:**

    - **200 OK:** If an admin user with the specified email is found, the response includes
      the admin user object (excluding password for security reasons).
    - **404 Not Found:** If no admin user with the specified email is found.
    - **500 Internal Server Error:** If an unexpected error occurs.

    **Raises:**

    - `HTTPException`: If an unexpected error occurs during database operations.
    """
    try:
        db = database.connect_to_mongo()
        admin_col = database.get_admin_collection(db)
        exist = admin_col.find_one({"email": email}, {"_id": 0, "password": 0})
        if not exist:
            return f"User with user email {email} does not exist"
        else:
            return exist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put("/update/address")
def update_admin_address(
    address: str, current_user=Depends(database.get_current_admin)
):
    """
    Updates the address of an admin user.

    **Path Parameter:**

    - **email (str):** The email address of the admin user to update.

    **Request Body:**

    - **address (str):** The new address for the admin user.

    **Authorization:**

    - Requires authentication as a current admin user (obtained through the
      `current_user` dependency).

    **Response:**

    - **200 OK:** If the admin user's address is successfully updated, the response includes
      the updated admin user object (excluding password for security reasons).
    - **401 Unauthorized:** If the user is not authorized to update admin addresses.
    - **404 Not Found:** If no admin user with the specified email is found.
    - **500 Internal Server Error:** If an unexpected error occurs.

    **Raises:**

    - `HTTPException`: If an unexpected error occurs during database operations.
    """
    try:
        db = database.connect_to_mongo()
        admin_col = database.get_admin_collection(db)
        email = current_user["email"]
        exist = admin_col.find_one({"email": email}, {"_id": 0})
        if exist:
            admin_col.update_one({"email": email}, {"$set": {"address": address}})
            return admin_col.find_one({"email": email}, {"_id": 0})
        else:
            return f"Admin with email : {email} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/delete")
def delete(current_user=Depends(database.get_current_admin)):
    """Deletes an admin user from the database.

    This endpoint allows authorized admins to remove their own account.

    Args:
        current_user (dict): The currently authenticated admin user, obtained
            through the `Depends(database.get_current_admin)` dependency.

    Returns:
        JSONResponse: A JSON response object with the following structure:
            - message (str): A success or error message indicating the outcome
              of the deletion operation.

    Raises:
        HTTPException: An HTTP exception with status code 500 (Internal Server Error)
            if an unexpected error occurs during database interaction.
    """
    try:
        db = database.connect_to_mongo()
        admin_col = database.get_admin_collection(db)
        email = current_user["email"]
        exist = admin_col.find_one({"email": email}, {"_id": 0, "password": 0})
        if not exist:
            return f"User with user email {email} does not exist"
        else:
            admin_col.delete_one({"email": email})
            return f"User with email : {email} is deleted from the record"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/deleteuser/{email}")
def delete_user(email: str, current_user=Depends(database.get_current_admin)):
    """Deletes a user from the database by email.

    This endpoint allows authorized admins to delete a user account by providing the user's email address.

    Args:
        email (str): The email address of the user to be deleted.
        current_user (dict): The currently authenticated admin user, obtained
            through the `Depends(database.get_current_admin)` dependency.

    Returns:
        JSONResponse: A JSON response object with the following structure:
            - message (str): A success or error message indicating the outcome
              of the deletion operation.

    Raises:
        HTTPException: An HTTP exception with an appropriate status code:
            - 404 (Not Found): If the user with the provided email address does not exist.
            - 500 (Internal Server Error): If an unexpected error occurs during database interaction.
    """
    try:
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        exist = user_col.find_one({"email": email}, {"_id": 0, "password": 0})
        if not exist:
            return f"User with user email {email} does not exist"
        else:
            user_col.delete_one({"email": email})
            return f"User with email : {email} is deleted from the record"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
