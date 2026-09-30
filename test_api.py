import httpx
import time

BASE = 'http://localhost:8000'
client = httpx.Client(timeout=10)

# Register and login
mobile = f'99999{int(time.time() * 1000) % 100000:05d}'
username = f'testuser{int(time.time())}'
reg_data = {'username': username, 'password': 'testpass123', 'full_name': 'Test Farmer', 'mobile': mobile}
resp = client.post(BASE + '/api/auth/register', json=reg_data)
print(f'Register: {resp.status_code}')

if resp.status_code == 200:
    # Login to get token
    login_data = {'username': username, 'password': 'testpass123'}
    resp = client.post(BASE + '/api/auth/token', data=login_data)
    print(f'Login: {resp.status_code}')
    if resp.status_code == 200:
        token = resp.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        print(f'Token obtained')
    else:
        headers = {}
        print('No token')
else:
    headers = {}
    print('Register failed')

# Test all endpoints
endpoints = [
    ('GET', '/health', {}, None),
    ('GET', '/api/auth/me', headers, None),
    ('GET', '/api/farmers', headers, None),
    ('GET', '/api/crops', headers, None),
    ('GET', '/api/weather', headers, None),
    ('GET', '/api/my-farm', headers, None),
    ('GET', '/api/my-farm/crops', headers, None),
    ('GET', '/api/soils', headers, None),
    ('GET', '/api/diseases', headers, None),
    ('GET', '/api/locations/countries', headers, None),
    ('GET', '/api/locations/states', headers, None),
    ('GET', '/api/locations/districts', {'Authorization': headers.get('Authorization', '')}, {'state_code': 'UP'}),
    ('GET', '/api/locations/blocks', {'Authorization': headers.get('Authorization', '')}, {'district_code': 'sitapur'}),
    ('POST', '/api/advisory', headers, {'crop_id': 1, 'question': 'test'}),
    ('POST', '/api/assistant', headers, {'query': 'test'}),
    ('POST', '/api/disease-detection', headers, {}),
    ('POST', '/api/pest/detect', headers, {}),
    ('POST', '/api/weed/detect', headers, {}),
    ('POST', '/api/nutrient-deficiency/detect', headers, {}),
    ('POST', '/api/growth-stage/detect', headers, {}),
    ('POST', '/api/predictions', headers, {}),
    ('POST', '/api/recommendations', headers, {}),
    ('POST', '/api/uploads', headers, {}),
]

print()
print('METHOD | PATH | HTTP STATUS | RESULT')
print('------ | ---- | ----------- | ------')

for method, path, h, body in endpoints:
    try:
        if method == 'GET':
            resp = client.get(BASE + path, headers=h, params=body)
        else:
            resp = client.post(BASE + path, headers=h, json=body)
        status = resp.status_code
        try:
            data = resp.json()
            if status < 400:
                result = 'OK'
            else:
                detail = data.get('detail', {})
                msg = detail.get('message', 'unknown') if isinstance(detail, dict) else str(detail)
                result = f'ERROR: {msg}'
        except:
            result = f'TEXT: {resp.text[:80]}'
        print(f'{method} | {path} | {status} | {result}')
    except Exception as e:
        print(f'{method} | {path} | ERROR | {e}')