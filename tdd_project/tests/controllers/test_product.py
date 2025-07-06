import datetime
from decimal import Decimal
from typing import List
from unittest.mock import patch

import pytest
from store.core.exceptions import InsertionException
from tests.factories import product_data
from fastapi import status


async def test_controller_create_should_return_success(client, products_url):
    response = await client.post(products_url, json=product_data())

    content = response.json()

    del content["created_at"]
    del content["updated_at"]
    del content["id"]

    assert response.status_code == status.HTTP_201_CREATED
    assert content == {
        "name": "Iphone 14 Pro Max",
        "quantity": 10,
        "price": "8.500",
        "status": True,
    }


async def test_controller_get_should_return_success(
    client, products_url, product_inserted
):
    response = await client.get(f"{products_url}{product_inserted.id}")

    content = response.json()

    del content["created_at"]
    del content["updated_at"]

    assert response.status_code == status.HTTP_200_OK
    assert content == {
        "id": str(product_inserted.id),
        "name": "Iphone 14 Pro Max",
        "quantity": 10,
        "price": "8.500",
        "status": True,
    }


async def test_controller_get_should_return_not_found(client, products_url):
    response = await client.get(f"{products_url}4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Product not found with filter: 4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    }


@pytest.mark.usefixtures("products_inserted")
async def test_controller_query_should_return_success(client, products_url):
    response = await client.get(products_url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), List)
    assert len(response.json()) > 1


async def test_controller_patch_should_return_success(
    client, products_url, product_inserted
):
    original_updated_at = product_inserted.updated_at

    response = await client.patch(
        f"{products_url}{product_inserted.id}", json={"price": "7.500"}
    )

    content = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert content["id"] == str(product_inserted.id)
    assert content["name"] == "Iphone 14 Pro Max"
    assert content["quantity"] == 10
    assert content["price"] == "7.500"
    assert content["status"] is True
    response_updated_at = datetime.fromisoformat(content["updated_at"])
    assert response_updated_at > original_updated_at
    assert datetime.utcnow() - response_updated_at < datetime.timedelta(seconds=5)
    assert datetime.fromisoformat(content["created_at"]) == product_inserted.created_at


async def test_controller_delete_should_return_no_content(
    client, products_url, product_inserted
):
    response = await client.delete(f"{products_url}{product_inserted.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_controller_delete_should_return_not_found(client, products_url):
    response = await client.delete(
        f"{products_url}4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Product not found with filter: 4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    }


async def test_controller_create_should_return_bad_request_on_insertion_error(
    client, products_url
):
    with patch(
        "store.usecases.product.ProductUsecase.create",
        side_effect=InsertionException("Product already exists."),
    ):
        response = await client.post(products_url, json=product_data())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Product already exists."}


async def test_controller_patch_should_return_bad_request_on_insertion_error(
    client, products_url, product_inserted
):
    with patch(
        "store.usecases.product.ProductUsecase.update",
        side_effect=InsertionException("Failed to update due to internal error."),
    ):
        response = await client.patch(
            f"{products_url}{product_inserted.id}", json={"price": "7.500"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Failed to update due to internal error."}


async def test_controller_patch_should_return_not_found(client, products_url):
    response = await client.patch(
        f"{products_url}4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca", json={"price": "7.500"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Product not found with filter: 4fd7cd35-a3a0-4c1f-a78d-d24aa81e7dca"
    }


@pytest.fixture
async def products_inserted_for_filter(mongo_client, client):
    await mongo_client.get_database()["products"].delete_many({})

    products_data_list = [
        {"name": "Monitor", "quantity": 10, "price": "4500.00", "status": True},
        {"name": "Mouse", "quantity": 5, "price": "6500.00", "status": True},
        {"name": "Keyboard", "quantity": 3, "price": "9000.00", "status": True},
        {"name": "Webcam", "quantity": 20, "price": "3000.00", "status": False},
        {"name": "Headset", "quantity": 15, "price": "7000.00", "status": True},
    ]
    inserted_products = []
    for p_data in products_data_list:
        response = await client.post("/products/", json=p_data)
        inserted_products.append(response.json())
    return inserted_products


@pytest.mark.usefixtures("products_inserted_for_filter")
async def test_controller_query_should_return_success_without_filter(
    client, products_url
):
    response = await client.get(products_url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), List)
    assert len(response.json()) == 5


async def test_controller_query_should_filter_by_price_range(
    client, products_url, products_inserted_for_filter
):
    response = await client.get(products_url + "?min_price=5000&max_price=8000")

    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert isinstance(content, List)
    assert len(content) == 2
    for product in content:
        price = Decimal(product["price"])
        assert price > Decimal("5000")
        assert price < Decimal("8000")
        assert product["name"] in ["Mouse", "Headset"]


async def test_controller_query_should_filter_by_min_price(
    client, products_url, products_inserted_for_filter
):
    response = await client.get(products_url + "?min_price=8000")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert len(content) == 1
    assert Decimal(content[0]["price"]) > Decimal("8000")
    assert content[0]["name"] == "Keyboard"


async def test_controller_query_should_filter_by_max_price(
    client, products_url, products_inserted_for_filter
):
    response = await client.get(products_url + "?max_price=5000")
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert len(content) == 2
    for product in content:
        price = Decimal(product["price"])
        assert price < Decimal("5000")
        assert product["name"] in ["Monitor", "Webcam"]
