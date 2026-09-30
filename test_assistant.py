import httpx
BASE = 'http://localhost:8000'
client = httpx.Client(timeout=10)
resp = client.post(BASE + '/api/auth/token', data={'username': 'testuser1787483843', 'password': 'testpass123'})
token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Test assistant with correct field name
resp = client.post(BASE + '/api/assistant', headers=headers, json={'text': '\u092e\u0947\u0930\u0940 \u092b\u0938\u0932 \u0915\u0947 \u0915\u094f \u0939\u093e\u0932 \u0939\u0948\u0902?'})
print('assistant:', resp.status_code, resp.json())