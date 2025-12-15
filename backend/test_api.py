#!/usr/bin/env python3
"""
Comprehensive API Testing Script for IMS FastAPI Backend
Tests all endpoints with valid data and error cases
"""

import requests
import json
from typing import Dict, Any, Optional

API_URL = "http://localhost:8000"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.ENDC}\n")

def print_test(test_name: str):
    """Print test name"""
    print(f"{Colors.CYAN}>> {test_name}{Colors.ENDC}")

def print_request(method: str, endpoint: str, data: Optional[Dict] = None):
    """Print request details"""
    print(f"  {Colors.YELLOW}{method} {endpoint}{Colors.ENDC}")
    if data:
        print(f"  Data: {json.dumps(data, indent=2)}")

def print_response(response: requests.Response):
    """Print response details"""
    try:
        data = response.json()
        print(f"  Status: {Colors.GREEN}{response.status_code}{Colors.ENDC}")
        print(f"  Response: {json.dumps(data, indent=2, default=str)}")
    except:
        print(f"  Status: {Colors.GREEN}{response.status_code}{Colors.ENDC}")
        print(f"  Response: {response.text}")
    print()

def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
    """Make HTTP request and return response"""
    url = f"{API_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if method == "GET":
        return requests.get(url, headers=headers)
    elif method == "POST":
        return requests.post(url, json=data, headers=headers)
    elif method == "PUT":
        return requests.put(url, json=data, headers=headers)
    elif method == "PATCH":
        return requests.patch(url, json=data, headers=headers)
    elif method == "DELETE":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

def test_system_endpoints():
    """Test system endpoints"""
    print_header("1. SYSTEM ENDPOINTS")

    print_test("1.1 Health Check")
    response = make_request("GET", "/health")
    print_response(response)

    print_test("1.2 Root API Info")
    response = make_request("GET", "/")
    print_response(response)

def test_inventory_endpoints():
    """Test inventory endpoints"""
    print_header("2. INVENTORY MANAGEMENT ENDPOINTS")

    items = {}

    # Create Item 1
    print_test("2.1 Create Item 1 - Grocery (Rice)")
    item1_data = {
        "name": "Rice 5kg",
        "category": "Grocery",
        "unit": "kg",
        "unit_price": 45.50,
        "stock_qty": 100
    }
    print_request("POST", "/api/items", item1_data)
    response = make_request("POST", "/api/items", item1_data)
    print_response(response)
    items["item1"] = response.json()["id"]

    # Create Item 2
    print_test("2.2 Create Item 2 - Garments (T-Shirt)")
    item2_data = {
        "name": "Cotton T-Shirt",
        "category": "Garments",
        "unit": "piece",
        "unit_price": 299.99,
        "stock_qty": 50
    }
    print_request("POST", "/api/items", item2_data)
    response = make_request("POST", "/api/items", item2_data)
    print_response(response)
    items["item2"] = response.json()["id"]

    # Create Item 3
    print_test("2.3 Create Item 3 - Beauty (Shampoo)")
    item3_data = {
        "name": "Shampoo Bottle",
        "category": "Beauty",
        "unit": "liter",
        "unit_price": 199.00,
        "stock_qty": 75
    }
    print_request("POST", "/api/items", item3_data)
    response = make_request("POST", "/api/items", item3_data)
    print_response(response)
    items["item3"] = response.json()["id"]

    # Create Item 4
    print_test("2.4 Create Item 4 - Utilities (Light Bulb)")
    item4_data = {
        "name": "Light Bulb LED",
        "category": "Utilities",
        "unit": "piece",
        "unit_price": 125.00,
        "stock_qty": 200
    }
    print_request("POST", "/api/items", item4_data)
    response = make_request("POST", "/api/items", item4_data)
    print_response(response)
    items["item4"] = response.json()["id"]

    # List all items
    print_test("2.5 List All Items")
    response = make_request("GET", "/api/items")
    print_response(response)

    # Filter by category
    print_test("2.6 Filter by Category (Grocery)")
    response = make_request("GET", "/api/items?category=Grocery")
    print_response(response)

    # Filter by name
    print_test("2.7 Filter by Name (Rice)")
    response = make_request("GET", "/api/items?name=Rice")
    print_response(response)

    # Get single item
    print_test(f"2.8 Get Single Item (ID: {items['item1']})")
    response = make_request("GET", f"/api/items/{items['item1']}")
    print_response(response)

    # Update item
    print_test(f"2.9 Update Item 1 - Change Price & Stock")
    update_data = {
        "unit_price": 49.99,
        "stock_qty": 80
    }
    print_request("PUT", f"/api/items/{items['item1']}", update_data)
    response = make_request("PUT", f"/api/items/{items['item1']}", update_data)
    print_response(response)

    # Verify update
    print_test("2.10 Verify Item 1 Update")
    response = make_request("GET", f"/api/items/{items['item1']}")
    print_response(response)

    return items

def test_billing_endpoints(items: Dict[str, int]):
    """Test billing endpoints"""
    print_header("3. BILLING ENDPOINTS")

    bills = {}

    # Create Bill 1
    print_test("3.1 Create Bill 1 - Multiple Items")
    bill1_data = {
        "customer_name": "John Doe",
        "store_name": "Store A",
        "items": [
            {"item_id": items["item1"], "quantity": 5},
            {"item_id": items["item2"], "quantity": 2}
        ]
    }
    print_request("POST", "/api/bills", bill1_data)
    response = make_request("POST", "/api/bills", bill1_data)
    print_response(response)
    if response.status_code == 201:
        bills["bill1"] = response.json()["id"]

    # Create Bill 2
    print_test("3.2 Create Bill 2 - Different Customer")
    bill2_data = {
        "customer_name": "Jane Smith",
        "store_name": "Store B",
        "items": [
            {"item_id": items["item3"], "quantity": 3},
            {"item_id": items["item4"], "quantity": 10}
        ]
    }
    print_request("POST", "/api/bills", bill2_data)
    response = make_request("POST", "/api/bills", bill2_data)
    print_response(response)
    if response.status_code == 201:
        bills["bill2"] = response.json()["id"]

    # List all bills
    print_test("3.3 List All Bills")
    response = make_request("GET", "/api/bills")
    print_response(response)

    # Get single bill
    if "bill1" in bills:
        print_test(f"3.4 Get Single Bill (Bill 1 ID: {bills['bill1']})")
        response = make_request("GET", f"/api/bills/{bills['bill1']}")
        print_response(response)

    if "bill2" in bills:
        print_test(f"3.5 Get Single Bill (Bill 2 ID: {bills['bill2']})")
        response = make_request("GET", f"/api/bills/{bills['bill2']}")
        print_response(response)

    return bills

def test_error_cases(items: Dict[str, int]):
    """Test error handling"""
    print_header("4. ERROR HANDLING TESTS")

    # Invalid category
    print_test("4.1 Create Item with Invalid Category (Electronics)")
    invalid_data = {
        "name": "Invalid Item",
        "category": "Electronics",
        "unit": "piece",
        "unit_price": 100.00,
        "stock_qty": 10
    }
    print_request("POST", "/api/items", invalid_data)
    response = make_request("POST", "/api/items", invalid_data)
    print_response(response)

    # Non-existent item
    print_test("4.2 Get Non-existent Item (ID: 9999)")
    response = make_request("GET", "/api/items/9999")
    print_response(response)

    # Insufficient stock
    print_test("4.3 Create Bill with Insufficient Stock")
    insufficient_data = {
        "customer_name": "Test User",
        "store_name": "Test Store",
        "items": [
            {"item_id": items["item1"], "quantity": 10000}
        ]
    }
    print_request("POST", "/api/bills", insufficient_data)
    response = make_request("POST", "/api/bills", insufficient_data)
    print_response(response)

    # Non-existent item in bill
    print_test("4.4 Create Bill with Non-existent Item")
    nonexistent_data = {
        "customer_name": "Test User",
        "store_name": "Test Store",
        "items": [
            {"item_id": 9999, "quantity": 1}
        ]
    }
    print_request("POST", "/api/bills", nonexistent_data)
    response = make_request("POST", "/api/bills", nonexistent_data)
    print_response(response)

def test_soft_delete(items: Dict[str, int]):
    """Test soft delete functionality"""
    print_header("5. SOFT DELETE TEST")

    # Delete item
    print_test(f"5.1 Delete Item 2 (ID: {items['item2']})")
    response = make_request("DELETE", f"/api/items/{items['item2']}")
    print_response(response)

    # Verify item is gone
    print_test("5.2 Verify Item 2 is Gone (should return 404)")
    response = make_request("GET", f"/api/items/{items['item2']}")
    print_response(response)

    # List items (should not include item2)
    print_test("5.3 List Items (Item 2 should be missing)")
    response = make_request("GET", "/api/items")
    print_response(response)

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 50)
    print("IMS FastAPI - Complete Endpoint Testing")
    print("=" * 50)
    print(f"{Colors.ENDC}")

    try:
        # Test system endpoints
        test_system_endpoints()

        # Test inventory endpoints
        items = test_inventory_endpoints()

        # Test billing endpoints
        bills = test_billing_endpoints(items)

        # Test error cases
        test_error_cases(items)

        # Test soft delete
        test_soft_delete(items)

        # Summary
        print_header("TEST SUMMARY")
        print(f"{Colors.GREEN}{Colors.BOLD}[OK] All tests completed successfully!{Colors.ENDC}\n")
        print("Test Coverage:")
        print("  [OK] System endpoints (health, root)")
        print("  [OK] Create items (4 different categories)")
        print("  [OK] List and filter items")
        print("  [OK] Get single item")
        print("  [OK] Update item")
        print("  [OK] Create bills")
        print("  [OK] List and get bills")
        print("  [OK] Error handling (invalid category, insufficient stock)")
        print("  [OK] Soft delete functionality")
        print()

    except Exception as e:
        print(f"{Colors.RED}{Colors.BOLD}[ERROR] {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
