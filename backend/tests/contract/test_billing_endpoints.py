"""
Contract tests for billing API endpoints (US6-8)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def sample_item(client):
    """Create a sample item for billing tests"""
    response = client.post("/api/items", json={
        "name": "Sugar",
        "category": "Grocery",
        "unit": "kg",
        "unit_price": "10.50",
        "stock_qty": "100.000",
    })
    return response.json()


class TestCreateBill:
    """Contract tests for POST /bills (US6)"""

    @pytest.mark.contract
    def test_create_bill_valid(self, client, sample_item):
        """Test: Valid bill → 201 status, bill with ID returned"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "10.000"}],
            "customer_name": "John Doe",
            "store_name": "Store 1",
        })
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["customer_name"] == "John Doe"
        assert data["store_name"] == "Store 1"
        assert "total_amount" in data
        assert data["bill_items"] is not None

    @pytest.mark.contract
    def test_create_bill_insufficient_stock(self, client, sample_item):
        """Test: Insufficient stock → 400 error"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "200.000"}],  # More than available
        })
        assert response.status_code == 400

    @pytest.mark.contract
    def test_create_bill_nonexistent_item(self, client):
        """Test: Non-existent item → 400 error"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": 99999, "quantity": "10.000"}],
        })
        assert response.status_code == 400

    @pytest.mark.contract
    def test_create_bill_zero_quantity(self, client, sample_item):
        """Test: Zero quantity → 422 error"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "0"}],
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_create_bill_negative_quantity(self, client, sample_item):
        """Test: Negative quantity → 422 error"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "-5.000"}],
        })
        assert response.status_code == 422

    @pytest.mark.contract
    def test_create_bill_decimal_quantity(self, client, sample_item):
        """Test: Decimal quantity → 201 status, accepted"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "2.500"}],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["bill_items"][0]["quantity"] == 2.5

    @pytest.mark.contract
    def test_create_bill_optional_names(self, client, sample_item):
        """Test: Optional customer/store names → 201 status with NULL values"""
        response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "5.000"}],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] is None
        assert data["store_name"] is None

    @pytest.mark.contract
    def test_create_bill_multiple_items(self, client):
        """Test: Bill with multiple items"""
        # Create two items
        item1_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item1 = item1_response.json()

        item2_response = client.post("/api/items", json={
            "name": "Flour",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "5.00",
            "stock_qty": "200.000",
        })
        item2 = item2_response.json()

        # Create bill with both items
        response = client.post("/api/bills", json={
            "items": [
                {"item_id": item1["id"], "quantity": "10.000"},
                {"item_id": item2["id"], "quantity": "5.000"},
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert len(data["bill_items"]) == 2


class TestGetBill:
    """Contract tests for GET /bills/{id} (US7)"""

    @pytest.mark.contract
    def test_get_bill_valid_id(self, client, sample_item):
        """Test: Valid bill ID → 200 status, complete bill returned"""
        # Create a bill
        create_response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "10.000"}],
            "customer_name": "John Doe",
        })
        bill_id = create_response.json()["id"]

        # Get the bill
        response = client.get(f"/api/bills/{bill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bill_id
        assert data["customer_name"] == "John Doe"
        assert "bill_items" in data
        assert len(data["bill_items"]) > 0

    @pytest.mark.contract
    def test_get_bill_nonexistent_id(self, client):
        """Test: Non-existent bill ID → 404 error"""
        response = client.get("/api/bills/99999")
        assert response.status_code == 404

    @pytest.mark.contract
    def test_get_bill_includes_all_line_items(self, client):
        """Test: Response includes all bill_items"""
        # Create two items
        item1_response = client.post("/api/items", json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        })
        item1 = item1_response.json()

        item2_response = client.post("/api/items", json={
            "name": "Flour",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "5.00",
            "stock_qty": "200.000",
        })
        item2 = item2_response.json()

        # Create bill with both items
        create_response = client.post("/api/bills", json={
            "items": [
                {"item_id": item1["id"], "quantity": "10.000"},
                {"item_id": item2["id"], "quantity": "5.000"},
            ],
        })
        bill_id = create_response.json()["id"]

        # Get the bill
        response = client.get(f"/api/bills/{bill_id}")
        data = response.json()
        assert len(data["bill_items"]) == 2
        assert all("item_name" in item for item in data["bill_items"])
        assert all("unit_price" in item for item in data["bill_items"])
        assert all("quantity" in item for item in data["bill_items"])
        assert all("line_total" in item for item in data["bill_items"])

    @pytest.mark.contract
    def test_get_bill_prices_as_strings(self, client, sample_item):
        """Test: Prices returned as strings, quantities as numbers"""
        # Create a bill
        create_response = client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "10.000"}],
        })
        bill_id = create_response.json()["id"]

        # Get the bill
        response = client.get(f"/api/bills/{bill_id}")
        data = response.json()
        assert isinstance(data["total_amount"], str)
        for item in data["bill_items"]:
            assert isinstance(item["unit_price"], str)
            assert isinstance(item["line_total"], str)
            assert isinstance(item["quantity"], (int, float))


class TestListBills:
    """Contract tests for GET /bills (US8)"""

    @pytest.mark.contract
    def test_list_bills_success(self, client, sample_item):
        """Test: GET /bills → returns all bills"""
        # Create a bill
        client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "5.000"}],
        })

        # List bills
        response = client.get("/api/bills")
        assert response.status_code == 200
        bills = response.json()
        assert isinstance(bills, list)
        assert len(bills) > 0

    @pytest.mark.contract
    def test_list_bills_includes_bill_items(self, client, sample_item):
        """Test: Each bill includes bill_items"""
        # Create a bill
        client.post("/api/bills", json={
            "items": [{"item_id": sample_item["id"], "quantity": "5.000"}],
        })

        # List bills
        response = client.get("/api/bills")
        bills = response.json()
        assert all("bill_items" in bill for bill in bills)
        assert all(len(bill["bill_items"]) > 0 for bill in bills)
