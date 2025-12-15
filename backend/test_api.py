"""Test REST API items endpoint after migration - with authentication"""
import requests

# Login to get token
login_resp = requests.post(
    'http://127.0.0.1:8000/auth/login',
    json={'email': 'testclaude@example.com', 'password': 'test123'}
)

if login_resp.status_code != 200:
    print(f'Login failed: {login_resp.text}')
    exit(1)

token = login_resp.json()['access_token']
print(f'Login successful! Token obtained.')

# Test GET /api/items with token
items_resp = requests.get(
    'http://127.0.0.1:8000/api/items',
    headers={'Authorization': f'Bearer {token}'}
)

print(f'\n=== REST API /api/items Response ===')
print(f'Status: {items_resp.status_code}')
items = items_resp.json()
print(f'Total items returned: {len(items)}')
print(f'\nItems:')
for item in items:
    print(f"  - {item['id']}: {item['name']} ({item['category']}) - Stock: {item['stock_qty']}")
