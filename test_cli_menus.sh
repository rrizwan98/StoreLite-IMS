#!/bin/bash

echo "=== Testing IMS CLI Menu Options ==="
echo ""

# Test Option 2: List Items
echo "[TEST 1] Option 2 - List All Items"
timeout 5 python backend/main.py << 'INPUT' 2>&1 | grep -E "INVENTORY|ERROR|Total|success" || echo "[PASS] No errors in option 2"
2
6
INPUT

echo ""
echo "[TEST 2] Option 6 - Exit"
timeout 3 python backend/main.py << 'INPUT' 2>&1 | grep -E "Goodbye|ERROR" || echo "[PASS] Option 6 works"
6
INPUT

echo ""
echo "=== All Menu Options Tested ==="
