#!/bin/bash

# API Testing Script for IMS FastAPI Backend
# This script tests all endpoints with valid data

API_URL="http://localhost:8000"
VALID_CATEGORIES=("Grocery" "Garments" "Beauty" "Utilities" "Other")
VALID_UNITS=("kg" "g" "liter" "ml" "piece" "box" "pack" "other")

echo "=========================================="
echo "IMS FastAPI - Complete Endpoint Testing"
echo "=========================================="
echo ""

# ============ SYSTEM ENDPOINTS ============
echo "=== 1. SYSTEM ENDPOINTS ==="
echo ""

echo "1.1 Health Check"
curl -X GET "${API_URL}/health" -H "Content-Type: application/json"
echo -e "\n"

echo "1.2 Root API Info"
curl -X GET "${API_URL}/" -H "Content-Type: application/json"
echo -e "\n"

# ============ INVENTORY ENDPOINTS ============
echo "=== 2. INVENTORY ENDPOINTS ==="
echo ""

echo "2.1 Create Item 1 - Grocery"
ITEM1=$(curl -s -X POST "${API_URL}/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rice 5kg",
    "category": "Grocery",
    "unit": "kg",
    "unit_price": 45.50,
    "stock_qty": 100
  }')
echo "$ITEM1" | jq '.'
ITEM1_ID=$(echo "$ITEM1" | jq -r '.id')
echo "Item 1 ID: $ITEM1_ID"
echo -e "\n"

echo "2.2 Create Item 2 - Garments"
ITEM2=$(curl -s -X POST "${API_URL}/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cotton T-Shirt",
    "category": "Garments",
    "unit": "piece",
    "unit_price": 299.99,
    "stock_qty": 50
  }')
echo "$ITEM2" | jq '.'
ITEM2_ID=$(echo "$ITEM2" | jq -r '.id')
echo "Item 2 ID: $ITEM2_ID"
echo -e "\n"

echo "2.3 Create Item 3 - Beauty"
ITEM3=$(curl -s -X POST "${API_URL}/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Shampoo Bottle",
    "category": "Beauty",
    "unit": "liter",
    "unit_price": 199.00,
    "stock_qty": 75
  }')
echo "$ITEM3" | jq '.'
ITEM3_ID=$(echo "$ITEM3" | jq -r '.id')
echo "Item 3 ID: $ITEM3_ID"
echo -e "\n"

echo "2.4 Create Item 4 - Utilities"
ITEM4=$(curl -s -X POST "${API_URL}/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Light Bulb LED",
    "category": "Utilities",
    "unit": "piece",
    "unit_price": 125.00,
    "stock_qty": 200
  }')
echo "$ITEM4" | jq '.'
ITEM4_ID=$(echo "$ITEM4" | jq -r '.id')
echo "Item 4 ID: $ITEM4_ID"
echo -e "\n"

echo "2.5 List All Items"
curl -s -X GET "${API_URL}/api/items" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "2.6 Filter by Category (Grocery)"
curl -s -X GET "${API_URL}/api/items?category=Grocery" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "2.7 Filter by Name (Rice)"
curl -s -X GET "${API_URL}/api/items?name=Rice" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "2.8 Get Single Item (Item 1)"
curl -s -X GET "${API_URL}/api/items/${ITEM1_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "2.9 Update Item 1 - Change price and stock"
curl -s -X PATCH "${API_URL}/api/items/${ITEM1_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "unit_price": 49.99,
    "stock_qty": 80
  }' | jq '.'
echo -e "\n"

echo "2.10 Verify Item 1 Update"
curl -s -X GET "${API_URL}/api/items/${ITEM1_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# ============ BILLING ENDPOINTS ============
echo "=== 3. BILLING ENDPOINTS ==="
echo ""

echo "3.1 Create Bill 1 - Multiple items"
BILL1=$(curl -s -X POST "${API_URL}/api/bills" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_name\": \"John Doe\",
    \"store_name\": \"Store A\",
    \"items\": [
      {
        \"item_id\": ${ITEM1_ID},
        \"quantity\": 5
      },
      {
        \"item_id\": ${ITEM2_ID},
        \"quantity\": 2
      }
    ]
  }")
echo "$BILL1" | jq '.'
BILL1_ID=$(echo "$BILL1" | jq -r '.id')
echo "Bill 1 ID: $BILL1_ID"
echo -e "\n"

echo "3.2 Create Bill 2 - Different customer"
BILL2=$(curl -s -X POST "${API_URL}/api/bills" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_name\": \"Jane Smith\",
    \"store_name\": \"Store B\",
    \"items\": [
      {
        \"item_id\": ${ITEM3_ID},
        \"quantity\": 3
      },
      {
        \"item_id\": ${ITEM4_ID},
        \"quantity\": 10
      }
    ]
  }")
echo "$BILL2" | jq '.'
BILL2_ID=$(echo "$BILL2" | jq -r '.id')
echo "Bill 2 ID: $BILL2_ID"
echo -e "\n"

echo "3.3 List All Bills"
curl -s -X GET "${API_URL}/api/bills" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "3.4 Get Single Bill (Bill 1)"
curl -s -X GET "${API_URL}/api/bills/${BILL1_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "3.5 Get Single Bill (Bill 2)"
curl -s -X GET "${API_URL}/api/bills/${BILL2_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# ============ ERROR CASES ============
echo "=== 4. ERROR HANDLING TESTS ==="
echo ""

echo "4.1 Create Item with Invalid Category (Electronics - should fail)"
curl -s -X POST "${API_URL}/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Item",
    "category": "Electronics",
    "unit": "piece",
    "unit_price": 100.00,
    "stock_qty": 10
  }' | jq '.'
echo -e "\n"

echo "4.2 Get Non-existent Item (ID: 9999)"
curl -s -X GET "${API_URL}/api/items/9999" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "4.3 Try to Create Bill with Insufficient Stock"
curl -s -X POST "${API_URL}/api/bills" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_name\": \"Test User\",
    \"store_name\": \"Test Store\",
    \"items\": [
      {
        \"item_id\": ${ITEM1_ID},
        \"quantity\": 10000
      }
    ]
  }" | jq '.'
echo -e "\n"

echo "4.4 Try to Create Bill with Non-existent Item"
curl -s -X POST "${API_URL}/api/bills" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "store_name": "Test Store",
    "items": [
      {
        "item_id": 9999,
        "quantity": 1
      }
    ]
  }' | jq '.'
echo -e "\n"

# ============ SOFT DELETE TEST ============
echo "=== 5. SOFT DELETE TEST ==="
echo ""

echo "5.1 Delete Item 2"
curl -s -X DELETE "${API_URL}/api/items/${ITEM2_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "5.2 Verify Item 2 is Gone (should return 404)"
curl -s -X GET "${API_URL}/api/items/${ITEM2_ID}" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "5.3 List Items (Item 2 should be missing)"
curl -s -X GET "${API_URL}/api/items" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="
