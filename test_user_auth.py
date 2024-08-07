import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from main import app
from model import User
from database import get_current_user, connect_to_mongo, get_user_collection

# Create a TestClient instance
client = TestClient(app)


# # Override the database connection and get_current_user dependency
# def override_connect_to_mongo():
#     return MagicMock()


@pytest.fixture
def mock_db():
    with patch("database.connect_to_mongo") as mongo_connect, patch(
        "database.get_user_collection"
    ) as get_mongo_collection:
        mongo_db = MagicMock()
        mongo_connect.return_value = mongo_db
        mongo_collection = MagicMock()
        get_mongo_collection.return_value = mongo_collection

        yield mongo_collection


def override_get_current_user():
    return {"email": "testuser@example.com", "role": "user"}


def override_get_current_admin():
    return {"email": "testadmin@example.com", "role": "admin"}


# app.dependency_overrides[connect_to_mongo] = override_connect_to_mongo
app.dependency_overrides[get_current_user] = override_get_current_user


# Test cases
def test_update_user_address_success(mock_db):
    mock_db.find_one.side_effect = [
        {
            "id": "user123",
            "username": "testuser",
            "email": "testuser@example.com",
            "address": "123 Test St",
            "password": "hashedpassword",
            "is_admin": False,
        },
        {
            "id": "user123",
            "username": "testuser",
            "email": "testuser@example.com",
            "address": "456 New Address",
            "password": "hashedpassword",
            "is_admin": False,
        },
    ]

    response = client.put(
        "/user/update/address/testuser@example.com",
        params={"address": "456 New Address"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "user123",
        "username": "testuser",
        "email": "testuser@example.com",
        "address": "456 New Address",
        "password": "hashedpassword",
        "is_admin": False,
    }


def test_update_user_address_user_not_found(mock_db):
    mock_db.find_one.return_value = None

    response = client.put(
        "/user/update/address/nonexistent@example.com",
        params={"address": "456 New Address"},
    )
    assert response.status_code == 200
    assert (
        response.json() == "Product with email : nonexistent@example.com does not exist"
    )


def test_update_user_address_unauthorized():
    app.dependency_overrides[get_current_user] = lambda: None

    response = client.put(
        "/user/update/address/testuser@example.com",
        params={"address": "456 New Address"},
    )
    print(response.json())
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_update_user_address_unauthorized_admin():
    app.dependency_overrides[get_current_user] = override_get_current_admin

    response = client.put(
        "/user/update/address/testuser@example.com",
        params={"address": "456 New Address"},
    )
    print(response.json())
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    # Restore the original override
    app.dependency_overrides[get_current_user] = override_get_current_user
