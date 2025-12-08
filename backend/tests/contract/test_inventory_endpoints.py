"""
Contract tests for inventory API endpoints (US1-5)
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models import Item
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateItem:
    """Contract tests for POST /items (US1)"""

    @pytest.mark.contract
    def test_create_item_success(self, client):
        """Test: Valid request → 201 status, item returned with ID"""
        response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Sugar"
        assert data["category"] == "Grocery"
        assert data["is_active"] is True

    @pytest.mark.contract
    def test_create_item_negative_price(self, client):
        """Test: Negative price → 422 with field error"""
        response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "-10.50",
            "stock_qty": "100.000",
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_create_item_negative_stock(self, client):
        """Test: Negative stock → 422 with field error"""
        response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "-100.000",
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_create_item_missing_required_field(self, client):
        """Test: Missing required field → 422"""
        response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            # Missing unit, unit_price, stock_qty
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_create_item_duplicate_name_allowed(self, client):
        """Test: Duplicate item names allowed → 201 status for both"""
        # Create first item
        response1 = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        assert response1.status_code == 201

        # Create second item with same name
        response2 = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Beverages",  # Different category
            "unit": "kg",
            "unit_price": "15.00",
            "stock_qty": "50.000",
        })
        assert response2.status_code == 201
        assert response1.json()["id"] != response2.json()["id"]


class TestListItems:
    """Contract tests for GET /items (US2)"""

    @pytest.mark.contract
    def test_list_items_no_filters(self, client):
        """Test: No filters → returns all active items"""
        # Create some items
        client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        client.post("/api/items", json={
            "name": "Flour",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "5.50",
            "stock_qty": "200.000",
        })

        response = client.get("/api/items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 2
        assert all(item["is_active"] for item in items)

    @pytest.mark.contract
    def test_list_items_name_filter_case_insensitive(self, client):
        """Test: name filter → case-insensitive match"""
        client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })

        response = client.get("/api/items?name=sugar")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["name"] == "Sugar"

    @pytest.mark.contract
    def test_list_items_category_filter(self, client):
        """Test: category filter → exact match"""
        client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        client.post("/api/items", json={
            "name": "Shirt",
            "category": "Garments",
            "unit": "piece",
            "unit_price": "500.00",
            "stock_qty": "50.000",
        })

        response = client.get("/api/items?category=Grocery")
        assert response.status_code == 200
        items = response.json()
        assert all(item["category"] == "Grocery" for item in items)

    @pytest.mark.contract
    def test_list_items_both_filters(self, client):
        """Test: both filters → AND logic"""
        client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })

        response = client.get("/api/items?name=sugar&category=Grocery")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["name"] == "Sugar"
        assert items[0]["category"] == "Grocery"

    @pytest.mark.contract
    def test_list_items_no_matches(self, client):
        """Test: no results → empty list with 200 status"""
        response = client.get("/api/items?name=nonexistent")
        assert response.status_code == 200
        items = response.json()
        assert items == []


class TestGetItem:
    """Contract tests for GET /items/{id} (US3)"""

    @pytest.mark.contract
    def test_get_item_valid_id(self, client):
        """Test: Valid ID → 200 status, item details returned"""
        # Create an item first
        create_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item_id = create_response.json()["id"]

        # Get the item
        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == "Sugar"

    @pytest.mark.contract
    def test_get_item_nonexistent_id(self, client):
        """Test: Non-existent ID → 404 error"""
        response = client.get("/api/items/99999")
        assert response.status_code == 404

    @pytest.mark.contract
    def test_get_item_invalid_id_format(self, client):
        """Test: Non-numeric ID → 422 validation error"""
        response = client.get("/api/items/invalid")
        assert response.status_code == 422


class TestUpdateItem:
    """Contract tests for PUT /items/{id} (US4)"""

    @pytest.mark.contract
    def test_update_item_price(self, client):
        """Test: Update price → 200 status, updated item returned"""
        # Create item
        create_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item_id = create_response.json()["id"]

        # Update price
        response = client.put(f"/api/items/{item_id}", json={
            "unit_price": "15.00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["unit_price"] == "15.00"

    @pytest.mark.contract
    def test_update_item_stock(self, client):
        """Test: Update stock → 200 status, updated item returned"""
        # Create item
        create_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item_id = create_response.json()["id"]

        # Update stock
        response = client.put(f"/api/items/{item_id}", json={
            "stock_qty": "150.000"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["stock_qty"] == Decimal("150.000")

    @pytest.mark.contract
    def test_update_item_negative_price(self, client):
        """Test: Negative price → 422"""
        # Create item
        create_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item_id = create_response.json()["id"]

        # Try to update with negative price
        response = client.put(f"/api/items/{item_id}", json={
            "unit_price": "-5.00"
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_update_nonexistent_item(self, client):
        """Test: Non-existent item → 404 error"""
        response = client.put("/api/items/99999", json={
            "unit_price": "15.00"
        })
        assert response.status_code == 404


class TestDeactivateItem:
    """Contract tests for DELETE /items/{id} (US5)"""

    @pytest.mark.contract
    def test_deactivate_item_success(self, client):
        """Test: Valid ID → 204 status, item marked inactive"""
        # Create item
        create_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item_id = create_response.json()["id"]

        # Deactivate
        response = client.delete(f"/api/items/{item_id}")
        assert response.status_code == 204

        # Verify item is no longer in list
        list_response = client.get("/api/items")
        items = list_response.json()
        assert all(item["id"] != item_id for item in items)

    @pytest.mark.contract
    def test_deactivate_nonexistent_item(self, client):
        """Test: Non-existent item → 404 error"""
        response = client.delete("/api/items/99999")
        assert response.status_code == 404
