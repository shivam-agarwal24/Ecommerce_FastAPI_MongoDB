from fastapi import APIRouter, Depends, HTTPException
import database
from model import Order

order_router = APIRouter(prefix="/order", tags=["Orders"])


@order_router.post("/create")
def create_order(current_user=Depends(database.get_current_user)):
    """
    Creates a new order for the currently authenticated user.

    This endpoint allows a user to create a new order in the system.
    It validates the user's authentication and assigns the user ID to the order
    before saving it to the database.

    Args:
        new_order (Order): The order data to be created. This should be a validated Order object.
        current_user (dict, optional): The current authenticated user. This is retrieved
            through dependency injection. Defaults to Depends(database.get_current_user).

    Returns:
        dict: A dictionary containing a success message upon successful creation.

    Raises:
        HTTPException:
            - 400: If the user ID is invalid.
            - 500: If an internal server error occurs during order creation.
    """
    invalid_user = HTTPException(status_code=400, detail="Invalid User Id given")
    try:
        new_order = Order()
        db = database.connect_to_mongo()
        user_col = database.get_user_collection(db)
        new_order.user_id = current_user["id"]
        user_exit = user_col.find_one({"id": new_order.user_id}, {"_id": 0})
        if user_exit:
            new_order.generate_id()
            new_order.add_products_from_cart(current_user["id"])
            new_order.calculate_amount()
            new_order.is_placed = True
            order_col = database.get_order_collection(db)
            order_col.insert_one(new_order.dict())
            new_order.delete_cart(current_user["id"])
            return {"Message": "Order Places Successfully"}
        else:
            raise invalid_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.get("/all")
def get_all_orders(
    current_user=Depends(database.get_current_admin),
    page_no: int = 1,
    page_size: int = 50,
):
    """
    Retrieves a paginated list of all orders in the system.

    This endpoint requires admin authentication and allows for retrieving orders
    in a paginated manner. It retrieves the total number of orders and then fetches
    a specific page based on the provided page number and size.

    Args:
        current_user (dict, optional): The current authenticated admin user. This is retrieved
            through dependency injection. Defaults to Depends(database.get_current_admin).
        page_no (int, optional): The page number to retrieve. Defaults to 1.
        page_size (int, optional): The number of orders to retrieve per page. Defaults to 50.

    Returns:
        dict: A dictionary containing information about the retrieved orders, including:
            - Page_No: The requested page number.
            - Page_Size: The number of orders per page.
            - Total: The total number of orders in the system.
            - Orders: A list of order data for the requested page.

    Raises:
        HTTPException:
            - 500: If an internal server error occurs during order retrieval.
    """
    try:
        db = database.connect_to_mongo()
        order_col = database.get_order_collection(db)
        skip_size = (page_no - 1) * page_size
        total_orders = order_col.count_documents({})
        result = order_col.find({}, {"_id": 0}).skip(skip_size).limit(page_size)
        result = list(result)

        response = {
            "Page_No": page_no,
            "Page_Size": page_size,
            "Total": total_orders,
            "Orders": result,
        }
        if len(result) == 0:
            return {"Message": "No More Orders Left in the Order Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.get("/user")
def get_user_orders(
    current_user=Depends(database.get_current_user),
    page_no: int = 1,
    page_size: int = 50,
):
    """
    Retrieves a paginated list of orders for the currently authenticated user.

    This endpoint allows a user to retrieve their own orders in a paginated manner.
    It retrieves the total number of user orders and then fetches a specific page
    based on the provided page number and size.

    Args:
        current_user (dict, optional): The current authenticated user. This is retrieved
            through dependency injection. Defaults to Depends(database.get_current_user).
        page_no (int, optional): The page number to retrieve. Defaults to 1.
        page_size (int, optional): The number of orders to retrieve per page. Defaults to 50.

    Returns:
        dict: A dictionary containing information about the retrieved orders, including:
            - Page_No: The requested page number.
            - Page_Size: The number of orders per page.
            - Total: The total number of user orders.
            - Orders: A list of order data for the requested page.

    Raises:
        HTTPException:
            - 500: If an internal server error occurs during order retrieval.
    """
    try:
        db = database.connect_to_mongo()
        order_col = database.get_order_collection(db)
        skip_size = (page_no - 1) * page_size
        total_orders = order_col.count_documents({"user_id": current_user["id"]})
        result = (
            order_col.find({"user_id": current_user["id"]}, {"_id": 0})
            .skip(skip_size)
            .limit(page_size)
        )
        result = list(result)

        response = {
            "Page_No": page_no,
            "Page_Size": page_size,
            "Total": total_orders,
            "Orders": result,
        }
        if len(result) == 0:
            return {"Message": "No More Orders Left in the Order Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@order_router.delete("/delete/{order_id}")
def delete_order(order_id: str, current_user=Depends(database.get_current_admin)):
    """
    Delete an order by its ID.

    This endpoint allows an admin to delete an order from the database.
    It checks if the order exists and, if so, deletes it. If the order
    does not exist, it returns a message indicating so.

    Parameters:
    - order_id (str): The ID of the order to be deleted.
    - current_user: The current authenticated admin user (dependency injection).

    Returns:
    - str: A message indicating whether the order was successfully deleted or if it did not exist.

    Raises:
    - HTTPException: If there is an issue with the database connection or any other error occurs.
    """
    try:
        db = database.connect_to_mongo()
        order_col = database.get_order_collection(db)
        exist = order_col.find_one({"id": order_id})
        if exist:
            order_col.delete_one({"id": order_id})
            return f"Order with ID {order_id} is deleted from the record"
        else:
            return f"Order with ID {order_id} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
