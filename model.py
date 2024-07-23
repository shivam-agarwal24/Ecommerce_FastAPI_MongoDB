from pydantic import BaseModel
from typing import Optional, List
from passlib.context import CryptContext
from fastapi import HTTPException
from uuid import uuid4


class Product(BaseModel):
    id: Optional[str | None] = None
    name: str
    description: str
    price: int | float
    quantity: int

    def generate_id(self):
        self.id = str(uuid4())


class User(BaseModel):
    id: Optional[str | None] = None
    username: str
    email: str
    address: str
    password: str
    is_admin: bool = False

    def generate_id(self):
        self.id = str(uuid4())

    def hash_password(self):
        pswd_context = CryptContext(schemes=["argon2"])
        self.password = pswd_context.hash(self.password)

    def verify_password(self, pswd):
        pswd_context = CryptContext(schemes=["argon2"])
        return pswd_context.verify(pswd, self.password)


class Admin(BaseModel):
    id: Optional[str | None] = None
    username: str
    email: str
    address: str
    password: str
    is_admin: bool = True

    def generate_id(self):
        self.id = str(uuid4())

    def hash_password(self):
        pswd_context = CryptContext(schemes=["argon2"])
        self.password = pswd_context.hash(self.password)

    def verify_password(self, pswd):
        pswd_context = CryptContext(schemes=["argon2"])
        return pswd_context.verify(pswd, self.password)


class TokenData(BaseModel):
    email: str
    role: str


class Cartitems(BaseModel):
    product_id: str
    quantity: int


class Cart(BaseModel):
    user_id: str
    items: List[Cartitems] = []

    def add_items(self, product_id: str, quantity: int):
        found = False
        for item in self.items:
            if item.product_id == product_id:
                found = True
                item.quantity += quantity
        if not found:
            self.items.append(Cartitems(product_id=product_id, quantity=quantity))

    def remove_item(self, product_id: str):
        self.items = [item for item in self.items if item.product_id != product_id]


class Order(BaseModel):
    id: Optional[str | None] = None
    user_id: Optional[str] = None
    product_ids: Optional[list] = None
    all_product: Optional[list] = []
    amount: Optional[int | float] = 0
    is_placed: bool = False

    def generate_id(self):
        self.id = str(uuid4())

    def add_products_from_cart(self, user_id: str):
        try:
            import database

            db = database.connect_to_mongo()
            cart_col = database.get_cart_collection(db)
            cart = cart_col.find_one({"user_id": user_id}, {"_id": 0})
            if cart:
                self.product_ids = cart.get("items")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def delete_cart(self, user_id: str):
        try:
            import database

            db = database.connect_to_mongo()
            cart_col = database.get_cart_collection(db)
            cart = cart_col.find_one({"user_id": user_id}, {"_id": 0})
            if cart:
                cart_col.delete_one({"user_id": user_id})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def calculate_amount(self):
        import database

        invalid_product_id_excrption = HTTPException(
            status_code=203, detail="Invalid Profuct ID Found"
        )
        db = database.connect_to_mongo()
        user_col = database.get_product_collection(db)
        try:
            if self.product_ids:
                for i in self.product_ids:
                    product = user_col.find_one(
                        {"id": i.get("product_id")}, {"_id": 0, "quantity": 0}
                    )

                    if not product:
                        raise invalid_product_id_excrption
                    else:
                        self.amount += product.get("price") * i.get("quantity")
                        if self.all_product:
                            self.all_product.append(dict(product))
                        else:
                            self.all_product = [dict(product)]

        except HTTPException:
            return invalid_product_id_excrption
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
