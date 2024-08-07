from fastapi.testclient import TestClient
from fastapi import HTTPException
import route.product_route
from unittest.mock import patch, MagicMock
import database
import pytest
from main import app


client = TestClient(app)

mock_data = [
    {
        "name": "Samsung S24",
        "description": "Superb Smartphone",
        "price": 65000,
        "quantity": 20,
    },
    {
        "name": "Realme Buds T300 Pro",
        "description": "Superb Bluetooth Earphone",
        "price": 2000,
        "quantity": 80,
    },
    {
        "name": "SG Cricket Bat",
        "description": "English Willow",
        "price": 25000,
        "quantity": 45,
    },
    {
        "name": "SG Test Ball",
        "description": "4-Piece and Extra thick Coating",
        "price": 20000,
        "quantity": 70,
    },
    {
        "name": "product5",
        "description": "Description of Product 5",
        "price": 1803,
        "quantity": 742,
    },
    {
        "name": "product6",
        "description": "Description of Product 6",
        "price": 3071,
        "quantity": 3990,
    },
    {
        "name": "product7",
        "description": "Description of Product 7",
        "price": 3497,
        "quantity": 4152,
    },
    {
        "name": "product8",
        "description": "Description of Product 8",
        "price": 234,
        "quantity": 2342,
    },
    {
        "name": "product9",
        "description": "Description of Product 9",
        "price": 185,
        "quantity": 1683,
    },
    {
        "name": "product10",
        "description": "Description of Product 10",
        "price": 5529,
        "quantity": 3486,
    },
]


@pytest.fixture
def mock_db():
    with patch("database.connect_to_mongo") as mongo_connect, patch(
        "database.get_product_collection"
    ) as get_mongo_collection:
        mongo_db = MagicMock()
        mongo_connect.return_value = mongo_db
        mongo_collection = MagicMock()
        get_mongo_collection.return_value = mongo_collection

        yield mongo_collection


@pytest.fixture
def mock_user():
    with patch("database.get_current_user") as mock_user:
        mock_user.return_value = {"email": "mockuser@gmail.com", "role": "user"}
        yield mock_user


@pytest.fixture
def mock_admin():
    with patch("database.get_current_admin") as mock_admin:
        mock_admin.return_value = {"email": "mockadmin@gmail.com", "role": "admin"}
        yield mock_admin


def test_show_product_success(mock_db, mock_user):
    mock_db.find.return_value.skip.return_value.limit.return_value = mock_data
    mock_db.count_documents.return_value = len(mock_data)

    response = client.get("/product/show/all", params={"page": 1, "size": 10})

    assert response.status_code == 200
    # print("*********************************************************************")
    # print(response.json())
    assert response.json() == {
        "page": 1,
        "size": 10,
        "total": len(mock_data),
        "products": mock_data,
    }


def test_show_product_success_by_name(mock_db, mock_user):
    mock_db.find.return_value.skip.return_value.limit.return_value = [mock_data[9]]
    mock_db.count_documents.return_value = 1

    response = client.get(
        "/product/show", params={"name": "product10", "page": 1, "size": 10}
    )

    assert response.status_code == 200
    # print("*********************************************************************")
    # print(response.json())
    # print([mock_data[9]])
    assert response.json() == {
        "page": 1,
        "size": 10,
        "total": 1,
        "products": [mock_data[9]],
    }


def test_show_product_empty(mock_db, mock_user):
    mock_db.find.return_value.skip.return_value.limit.return_value = []
    mock_db.count_documents.return_value = 0

    response = client.get(
        "/product/show", params={"name": "product10", "page": 1, "size": 10}
    )

    assert response.status_code == 200
    # print(response.json())
    assert response.json() == {
        "message": "No More Collections Left in the Products Collection"
    }


def test_show_product_exception(mock_db, mock_user, mock_admin):
    mock_db.find.side_effect = Exception("Some Internal Exception occured")

    response = client.get(
        "/product/show", params={"name": "product10", "page": 1, "size": 10}
    )
    print(mock_admin.return_value)
    assert response.status_code == 500
    assert response.json() == {"detail": "Some Internal Exception occured"}
