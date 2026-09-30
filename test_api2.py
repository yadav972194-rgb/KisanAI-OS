import httpx
import time

BASE = 'http://localhost:8000'
client = httpx.Client(timeout=15)

# Register and login
mobile = f'99999{int(time.time() * 1000) % 100000:05d}'
username = f'testuser{int(time.time())}'
reg_data = {'username': username, 'password': 'testpass123', 'full_name': 'Test Farmer', 'mobile': mobile}
resp = client.post(BASE + '/api/auth/register', json=reg_data)

login_data = {'username': username, 'password': 'testpass123'}
resp = client.post(BASE + '/api/auth/token', data=login_data)
token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Create farm
farm_data = {'village': 'Test Village', 'district': 'Sitapur', 'state': 'Uttar Pradesh', 'farm_size': 5.0}
resp = client.post(BASE + '/api/my-farm', headers=headers, json=farm_data)

# Add a crop
crop_data = {'crop_name': 'Wheat', 'season': 'Rabi', 'duration_days': 120, 'water_requirement': 'Medium'}
resp = client.post(BASE + '/api/my-farm/crops', headers=headers, json=crop_data)
print('Add crop:', resp.status_code, resp.json())

# Test all endpoints with proper data
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
    ('GET', '/api/locations/districts', headers, {'state_code': 'UP'}),
    ('GET', '/api/locations/blocks', headers, {'district_code': 'sitapur'}),
    ('POST', '/api/advisory', headers, {'crop_id': 1, 'question': 'When to harvest wheat?'}),
    ('POST', '/api/assistant', headers, {'query': 'मेरी फसल के क्या हाल हैं?'}),
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
                code = detail.get('code', '') if isinstance(detail, dict) else ''
                result = f'ERROR[{code}]: {msg}'
        except:
            result = f'TEXT: {resp.text[:80]}'
        print(f'{method} | {path} | {status} | {result}')
    except Exception as e:
        print(f'{method} | {path} | ERROR | {e}')