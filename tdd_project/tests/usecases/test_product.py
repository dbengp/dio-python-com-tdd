import datetime
from decimal import Decimal
from typing import List
from unittest.mock import patch
from uuid import UUID

import pymongo
import pytest
from store.core.exceptions import InsertionException, NotFoundException
from store.schemas.product import ProductIn, ProductOut, ProductUpdateOut
from store.usecases.product import product_usecase


async def test_usecases_create_should_return_success(product_in):
    result = await product_usecase.create(body=product_in)

    assert isinstance(result, ProductOut)
    assert result.name == "Iphone 14 Pro Max"


async def test_usecases_get_should_return_success(product_inserted):
    result = await product_usecase.get(id=product_inserted.id)

    assert isinstance(result, ProductOut)
    assert result.name == "Iphone 14 Pro Max"


async def test_usecases_get_should_not_found():
    with pytest.raises(NotFoundException) as err:
        await product_usecase.get(id=UUID("1e4f214e-85f7-461a-89d0-a751a32e3bb9"))

    assert (
        err.value.message
        == "Product not found with filter: 1e4f214e-85f7-461a-89d0-a751a32e3bb9"
    )


@pytest.mark.usefixtures("products_inserted")
async def test_usecases_query_should_return_success():
    result = await product_usecase.query()

    assert isinstance(result, List)
    assert len(result) > 1


async def test_usecases_update_should_return_success(product_up, product_inserted):
    original_updated_at = product_inserted.updated_at

    product_up.price = "7.500"
    result = await product_usecase.update(id=product_inserted.id, body=product_up)

    assert isinstance(result, ProductUpdateOut)
    assert result.updated_at > original_updated_at
    assert datetime.utcnow() - result.updated_at < datetime.timedelta(seconds=5)
    assert result.price == 7.500


async def test_usecases_delete_should_return_success(product_inserted):
    result = await product_usecase.delete(id=product_inserted.id)

    assert result is True


async def test_usecases_delete_should_not_found():
    with pytest.raises(NotFoundException) as err:
        await product_usecase.delete(id=UUID("1e4f214e-85f7-461a-89d0-a751a32e3bb9"))

    assert (
        err.value.message
        == "Product not found with filter: 1e4f214e-85f7-461a-89d0-a751a32e3bb9"
    )


async def test_usecases_create_should_raise_insertion_exception_on_db_error(product_in):
    with patch.object(
        product_usecase.collection,
        "insert_one",
        side_effect=Exception("Simulated DB Error"),
    ):
        with pytest.raises(InsertionException) as excinfo:
            await product_usecase.create(body=product_in)
        assert "Failed to insert product: Simulated DB Error" == excinfo.value.message


async def test_usecases_create_should_raise_insertion_exception_on_duplicate_key(
    product_in,
):
    with patch.object(
        product_usecase.collection,
        "insert_one",
        side_effect=pymongo.errors.DuplicateKeyError("Duplicate key error"),
    ):
        with pytest.raises(InsertionException) as excinfo:
            await product_usecase.create(body=product_in)
        assert "Product with this name already exists." == excinfo.value.message


async def test_usecases_update_should_raise_insertion_exception_on_db_error(
    product_up, product_inserted
):
    with patch.object(
        product_usecase.collection,
        "find_one_and_update",
        side_effect=Exception("Simulated DB Update Error"),
    ):
        with pytest.raises(InsertionException) as excinfo:
            await product_usecase.update(id=product_inserted.id, body=product_up)
        assert (
            "Failed to update product: Simulated DB Update Error"
            == excinfo.value.message
        )


async def test_usecases_update_should_raise_not_found(product_up):
    with patch.object(
        product_usecase.collection, "find_one_and_update", return_value=None
    ):
        with pytest.raises(NotFoundException) as excinfo:
            await product_usecase.update(
                id=UUID("1e4f214e-85f7-461a-89d0-a751a32e3bb9"), body=product_up
            )
        assert (
            "Product not found with filter: 1e4f214e-85f7-461a-89d0-a751a32e3bb9"
            == excinfo.value.message
        )


@pytest.fixture
async def products_with_varied_prices(mongo_client):
    await mongo_client.get_database()["products"].delete_many({})

    products_data_list = [
        ProductIn(
            name="Laptop Basic", quantity=10, price=Decimal("4500.00"), status=True
        ),
        ProductIn(name="Laptop Mid", quantity=5, price=Decimal("6500.00"), status=True),
        ProductIn(
            name="Laptop High", quantity=3, price=Decimal("9000.00"), status=True
        ),
        ProductIn(name="Tablet", quantity=20, price=Decimal("3000.00"), status=False),
        ProductIn(
            name="Smartphone", quantity=15, price=Decimal("7000.00"), status=True
        ),
    ]
    inserted_products = []
    for p_in in products_data_list:
        inserted_products.append(await product_usecase.create(body=p_in))
    return inserted_products


async def test_usecases_query_should_return_all_products_without_filter(
    products_with_varied_prices,
):
    result = await product_usecase.query()
    assert isinstance(result, List)
    assert len(result) == len(products_with_varied_prices)


async def test_usecases_query_should_filter_by_price_range(products_with_varied_prices):
    min_price = Decimal("5000")
    max_price = Decimal("8000")
    result = await product_usecase.query(min_price=min_price, max_price=max_price)

    assert isinstance(result, List)
    assert len(result) == 2
    for product in result:
        assert product.price > min_price
        assert product.price < max_price
        assert product.name in ["Laptop Mid", "Smartphone"]


async def test_usecases_query_should_filter_by_min_price(products_with_varied_prices):
    min_price = Decimal("8000")
    result = await product_usecase.query(min_price=min_price)

    assert isinstance(result, List)
    assert len(result) == 1
    assert result[0].price > min_price
    assert result[0].name == "Laptop High"


async def test_usecases_query_should_filter_by_max_price(products_with_varied_prices):
    max_price = Decimal("5000")
    result = await product_usecase.query(max_price=max_price)

    assert isinstance(result, List)
    assert len(result) == 2
    for product in result:
        assert product.price < max_price
        assert product.name in ["Laptop Basic", "Tablet"]
