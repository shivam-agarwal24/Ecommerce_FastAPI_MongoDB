from fastapi import APIRouter, HTTPException, Depends
from model import Cart
import database


cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get("/items")
def get_items(current_user=Depends(database.get_current_user)):
    """
    Retrieve all items in the current user's cart.

    This endpoint fetches all items in the cart of the currently logged-in user.

    Args:
        current_user (dict): The currently logged-in user. This is automatically injected by the
                             Depends function which uses the get_current_user dependency.

    Returns:
        dict: A dictionary containing all items in the user's cart. If the cart is empty,
              a message indicating that the cart is empty is returned.

    Raises:
        HTTPException: If an internal server error occurs, an HTTPException with status code 500 and
                       the error details is raised.
    """
    try:
        db = database.connect_to_mongo()
        cart_col = database.get_cart_collection(db)
        cart = cart_col.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if cart:
            return cart
        else:
            return {"Message": "The Cart is Empty"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@cart_router.put("/add")
def add_item(
    product_id: str, quantity: int = 1, current_user=Depends(database.get_current_user)
):
    """
    Add an item to the current user's cart.

    This endpoint allows the user to add a specified quantity of an item to their cart.

    Args:
        product_id (str): The ID of the product to be added to the cart.
        quantity (int, optional): The quantity of the product to be added. Defaults to 1.
        current_user (dict): The currently logged-in user. This is automatically injected by the
                             Depends function which uses the get_current_user dependency.

    Returns:
        dict: A message indicating the item was added successfully.

    Raises:
        HTTPException: If an internal server error occurs, an HTTPException with status code 500 and
                       the error details is raised.
    """
    try:
        db = database.connect_to_mongo()
        cart_col = database.get_cart_collection(db)
        cart = cart_col.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if not cart:
            cart = Cart(user_id=current_user["id"], items=[])
        else:
            cart = Cart(**cart)
        cart.add_items(product_id=product_id, quantity=quantity)
        cart_col.update_one(
            {"user_id": current_user["id"]}, {"$set": cart.dict()}, upsert=True
        )
        return {"Message": "Item added to cart successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@cart_router.put("/remove")
def remove_item(product_id: str, current_user=Depends(database.get_current_user)):
    """
    Remove an item from the current user's cart.

    This endpoint allows the user to remove a specified item from their cart.

    Args:
        product_id (str): The ID of the product to be removed from the cart.
        current_user (dict): The currently logged-in user. This is automatically injected by the
                             Depends function which uses the get_current_user dependency.

    Returns:
        dict: A message indicating the item was removed successfully or that the item was not found in the cart.

    Raises:
        HTTPException: If the cart is not found, an HTTPException with status code 404 is raised.
                       If an internal server error occurs, an HTTPException with status code 500 and
                       the error details is raised.
    """
    try:
        db = database.connect_to_mongo()
        cart_col = database.get_cart_collection(db)
        cart = cart_col.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        else:
            cart = Cart(**cart)
        cart_products = [i.product_id for i in cart.items]
        if product_id in cart_products:
            cart.remove_item(product_id=product_id)
            cart_col.update_one(
                {"user_id": current_user["id"]}, {"$set": cart.dict()}, upsert=True
            )
            return {"Message": "Item remove from cart successfully"}
        else:
            return {"Message": "Item not found in Cart"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@cart_router.delete("/delete")
def delete_cart(current_user=Depends(database.get_current_user)):
    """
    Delete all items in the current user's cart.

    This endpoint allows the user to delete all items from their cart.

    Args:
        current_user (dict): The currently logged-in user. This is automatically injected by the
                             Depends function which uses the get_current_user dependency.

    Returns:
        dict: A message indicating all items in the cart have been deleted.

    Raises:
        HTTPException: If the cart is not found, an HTTPException with status code 404 is raised.
                       If an internal server error occurs, an HTTPException with status code 500 and
                       the error details is raised.
    """
    try:
        db = database.connect_to_mongo()
        cart_col = database.get_cart_collection(db)
        cart = cart_col.find_one({"user_id": current_user["id"]}, {"_id": 0})

        if not cart:
            raise HTTPException(status_code=404, detail="Cart not Found")
        else:
            cart = cart_col.delete_one({"user_id": current_user["id"]})
            return {"Message": "All the items in the cart are now deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
