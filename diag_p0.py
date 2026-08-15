import json
import random
import sys
import urllib.request
import urllib.error
import time

BASE = "http://127.0.0.1:8712"


def req(method, path, body=None, token=None, form=False, timeout=20):
    url = BASE + path
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}
    except Exception as e:
        return None, {"error": str(e)}


def mobile():
    return f"9{random.randint(100000000, 999999999)}"


def username(p):
    return f"{p}{random.randint(100000, 999999)}"


fails = []
for cycle in range(5):
    uname = username("p0cy")
    pw = "password123"
    mob = mobile()

    status, body = req("POST", "/api/auth/register",
                       {"username": uname, "password": pw, "full_name": "P0 Farmer",
                        "mobile": mob, "role": "farmer"})
    if status != 200:
        fails.append(f"cycle{cycle} register failed: {status} {body}")
        continue

    status, body = req("POST", "/api/auth/token", {"username": uname, "password": pw}, form=True)
    if status != 200:
        fails.append(f"cycle{cycle} login failed: {status} {body}")
        continue
    token = body["access_token"]

    status, body = req("GET", "/api/auth/me", token=token)
    if status != 200:
        fails.append(f"cycle{cycle} me failed after login: {status} {body}")
        continue

    # LOGOUT
    status, body = req("POST", "/api/auth/logout", {}, token=token)
    if status != 200:
        fails.append(f"cycle{cycle} logout failed: {status} {body}")
        continue

    # LOGIN AGAIN WITH SAME ACCOUNT
    status, body = req("POST", "/api/auth/token", {"username": uname, "password": pw}, form=True)
    if status != 200:
        fails.append(f"cycle{cycle} re-login failed: {status} {body}")
        continue
    token2 = body["access_token"]

    status, body = req("GET", "/api/auth/me", token=token2)
    if status != 200:
        fails.append(f"cycle{cycle} me failed after re-login: {status} {body}")
        continue

    # LOGOUT again, login again
    req("POST", "/api/auth/logout", {}, token=token2)
    status, body = req("POST", "/api/auth/token", {"username": uname, "password": pw}, form=True)
    if status != 200:
        fails.append(f"cycle{cycle} 3rd login failed: {status} {body}")
        continue
    status, body = req("GET", "/api/auth/me", token=body["access_token"])
    if status != 200:
        fails.append(f"cycle{cycle} me failed after 3rd login: {status} {body}")
        continue

print(f"P0 diagnostic: 5 cycles done, fails={len(fails)}")
for f in fails:
    print("  FAIL:", f)

# Also test wrong-password classification & no-session-wipe
uname = username("p0wp")
mob = mobile()
req("POST", "/api/auth/register",
    {"username": uname, "password": pw, "full_name": "P0 WP", "mobile": mob, "role": "farmer"})
status, body = req("POST", "/api/auth/token", {"username": uname, "password": pw}, form=True)
token = body["access_token"]
status, body = req("POST", "/api/auth/token", {"username": uname, "password": "wrongpw"}, form=True)
print("Wrong password:", status, body)
status, body = req("GET", "/api/auth/me", token=token)
print("Session after failed login:", status, body.get("username"))
if status != 200:
    fails.append("failed login wiped a live session")

# nonexistent user login
status, body = req("POST", "/api/auth/token", {"username": "nouser_zzz", "password": "x"}, form=True)
print("Nonexistent user login:", status, body)

sys.exit(1 if fails else 0)
