from fastapi.testclient import TestClient
from fastapi import HTTPException
import route.user_route
from unittest.mock import patch, MagicMock
import database
import pytest
from main import app
from model import User

client = TestClient(app)


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


@pytest.fixture
def new_user_data():
    return User(
        email="newuser@example.com",
        username="newuser",
        password="password123",
        address="new address",
    )


def test_add_user_success(mock_db, new_user_data):
    # Setup mock responses
    # mock_db.find_one.return_value = None
    mock_db.find_one.side_effect = [None, new_user_data.dict()]
    mock_db.insert_one.return_value = None
    # mock_db.find_one.return_value = new_user_data.dict()

    # API call
    response = client.post("/user/add", json=new_user_data.dict())

    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "message": f"User added with Username : {new_user_data.username} and User ID : {new_user_data.id}"
    }


def test_add_user_already_exists(mock_db, new_user_data):
    # Setup mock response for existing user
    mock_db.find_one.return_value = new_user_data.dict()

    # API call
    response = client.post("/user/add", json=new_user_data.dict())

    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "message": f"User with email id {new_user_data.email} already exist"
    }


def test_add_user_internal_server_error(mock_db, new_user_data):
    # Setup mock to raise exception
    mock_db.find_one.side_effect = Exception("Some Internal Exception occured")

    # API call
    response = client.post("/user/add", json=new_user_data.dict())

    # Assertions
    assert response.status_code == 500
    assert response.json() == {"detail": "Some Internal Exception occured"}
