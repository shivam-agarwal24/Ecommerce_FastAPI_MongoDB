from fastapi import APIRouter, Depends, HTTPException
from model import Product
import database
from database import get_current_admin

product_router = APIRouter(prefix="/product", tags=["Product"])


@product_router.post("/add")
def add_product(new_prod: Product, current_user=Depends(get_current_admin)):
    """
    This API endpoint allows authorized admins to add a new product to the database.

    Args:
        new_prod (Product): The product data to be added. (Expected data format as per the Product model)
        current_user (User, optional): The currently logged-in admin user. Depends on get_current_admin dependency.

    Returns:
        dict: A dictionary containing a success message upon successful product addition.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        new_prod.generate_id()
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)
        prod_col.insert_one(new_prod.dict())
        return {"Message": "Product added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@product_router.get("/show/all")
def show_all_product(page: int = 1, size: int = 50):
    """
    This API endpoint retrieves a paginated list of all products in the database.

    Args:
        page (int, optional): The current page number (defaults to 1).
        size (int, optional): The number of products to retrieve per page (defaults to 50).

    Returns:
        dict: A dictionary containing information about the retrieved products, including:
            * page (int): The current page number.
            * size (int): The number of products retrieved per page.
            * total (int): The total number of products in the database.
            * products (list): A list of product data (as per the Product model) for the current page.
            * message (str, optional): A message indicating no products were found if applicable.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)

        skip = (page - 1) * size

        total_products = prod_col.count_documents({})

        result = prod_col.find({}, {"_id": 0}).skip(skip).limit(size)
        result = list(result)

        response = {
            "page": page,
            "size": size,
            "total": total_products,
            "products": result,
        }

        if len(result) == 0:
            return {"message": "No More Collections Left in the Products Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@product_router.get("/show")
def show_product(name: str, page: int = 1, size: int = 50):
    """
    This API endpoint retrieves a paginated list of all products in the database.

    Args:
        page (int, optional): The current page number (defaults to 1).
        size (int, optional): The number of products to retrieve per page (defaults to 50).

    Returns:
        dict: A dictionary containing information about the retrieved products, including:
            * page (int): The current page number.
            * size (int): The number of products retrieved per page.
            * total (int): The total number of products in the database.
            * products (list): A list of product data (as per the Product model) for the current page.
            * message (str, optional): A message indicating no products were found if applicable.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)

        skip = (page - 1) * size

        total_products = prod_col.count_documents({})

        result = prod_col.find({"name": name}, {"_id": 0}).skip(skip).limit(size)
        result = list(result)

        response = {
            "page": page,
            "size": size,
            "total": total_products,
            "products": result,
        }

        if len(result) == 0:
            return {"message": "No More Collections Left in the Products Collection"}
        else:
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @product_router.get("/show/{id}")
# def show_product_id(id: str):
#     """
#     This API endpoint retrieves details of a specific product by its ID.

#     Args:
#         id (str): The unique ID of the product to retrieve.

#     Returns:
#         dict: A dictionary containing the product data (as per the Product model) if found,
#                or a message indicating the product was not found.

#     Raises:
#         HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
#     """
#     try:
#         db = database.connect_to_mongo()
#         prod_col = database.get_product_collection(db)
#         print(id)
#         result = prod_col.find_one({"id": id}, {"_id": 0})
#         if result:
#             return result
#         else:
#             return f"Product with id : {id} does not exist"
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@product_router.put("/update/price/{id}")
def update_product_price(
    id: str, price: int | float, current_user=Depends(get_current_admin)
):
    """
    This API endpoint allows authorized admins to update the price of a product by its ID.

    Args:
        id (str): The unique ID of the product to update.
        price (int | float): The new price for the product.
        current_user (User, optional): The currently logged-in admin user. Depends on get_current_admin dependency.

    Returns:
        dict: A dictionary containing the updated product data (as per the Product model) if successful,
               or a message indicating the product was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)
        exist = prod_col.find_one({"id": id})
        if exist:
            prod_col.update_one({"id": id}, {"$set": {"price": price}})
            return prod_col.find_one({"id": id}, {"_id": 0})
        else:
            return f"Product with id : {id} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@product_router.put("/update/quantity/{id}")
def update_product_quantity(
    id: str, quantity: int, current_user=Depends(get_current_admin)
):
    """
    This API endpoint allows authorized admins to update the quantity of a product by its ID.

    Args:
        id (str): The unique ID of the product to update.
        quantity (int): The new quantity for the product.
        current_user (User, optional): The currently logged-in admin user. Depends on get_current_admin dependency.

    Returns:
        dict: A dictionary containing the updated product data (as per the Product model) if successful,
               or a message indicating the product was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)
        exist = prod_col.find_one({"id": id})
        if exist:
            prod_col.update_one({"id": id}, {"$set": {"quantity": quantity}})
            return prod_col.find_one({"id": id}, {"_id": 0})
        else:
            return f"Product with id : {id} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@product_router.delete("/delete/{id}", dependencies=[Depends(get_current_admin)])
def delete_product(id: str):
    """
    This API endpoint allows authorized admins to delete a product by its ID.

    Args:
        id (str): The unique ID of the product to delete.

    Returns:
        dict: A dictionary containing a success message upon successful product deletion,
               or a message indicating the product was not found.

    Raises:
        HTTPException: An HTTPException with status code 500 and details about the error if something goes wrong.
    """
    try:
        db = database.connect_to_mongo()
        prod_col = database.get_product_collection(db)
        exist = prod_col.find_one({"id": id})
        if exist:
            prod_col.delete_one({"id": id})
            return f"Product with id : {id} is deleted from the record"
        else:
            return f"Product with id : {id} does not exist"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
