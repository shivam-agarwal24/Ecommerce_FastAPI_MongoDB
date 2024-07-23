from fastapi import FastAPI
from route.product_route import product_router
from route.user_route import user_router
from route.admin_route import admin_router
from route.auth import auth_router
from route.order_route import order_router
from route.cart_route import cart_router


app = FastAPI()

app.include_router(product_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(cart_router)
