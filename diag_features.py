import json
import random
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8712"


def req(method, path, body=None, token=None, form=False, files=None, timeout=30):
    url = BASE + path
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files is not None:
        import uuid
        boundary = uuid.uuid4().hex
        buf = bytearray()
        for field, (fname, content, ctype) in files.items():
            buf += f"--{boundary}\r\n".encode()
            buf += f'Content-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'.encode()
            buf += f"Content-Type: {ctype}\r\n\r\n".encode()
            buf += content + b"\r\n"
        if body is not None:
            for k, v in body.items():
                buf += f"--{boundary}\r\n".encode()
                buf += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
                buf += str(v).encode() + b"\r\n"
        buf += f"--{boundary}--\r\n".encode()
        data = bytes(buf)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
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


def uname(p):
    return f"{p}{random.randint(100000, 999999)}"


fails = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label} {detail}")
    if not ok:
        fails.append(label)


def register_and_login(prefix):
    u = uname(prefix)
    p = "password123"
    s, b = req("POST", "/api/auth/register",
               {"username": u, "password": p, "full_name": "Diag Farmer",
                "mobile": mobile(), "role": "farmer"})
    assert s == 200, (s, b)
    s, b = req("POST", "/api/auth/token", {"username": u, "password": p}, form=True)
    assert s == 200, (s, b)
    return u, b["access_token"]


# ================= P1: MY FARM =================
print("== P1 MY FARM ==")
u1, t1 = register_and_login("mf")
u2, t2 = register_and_login("mf2")

# No farm yet -> 404 -> null on client
s, b = req("GET", "/api/my-farm", token=t1)
check("no-farm returns 404", s == 404, f"(got {s})")

# Create farm
s, b = req("POST", "/api/my-farm",
           {"village": "Rampur", "district": "Sitapur", "state": "Uttar Pradesh", "farm_size": 3.5}, token=t1)
check("create farm", s == 200, b if s != 200 else "")

# Fetch farm
s, b = req("GET", "/api/my-farm", token=t1)
check("fetch farm", s == 200 and b.get("village") == "Rampur", f"(got {s})")

# Update farm
s, b = req("PUT", "/api/my-farm",
           {"village": "Ganeshpur", "district": "Sitapur", "state": "Uttar Pradesh", "farm_size": 4.0}, token=t1)
check("update farm", s == 200, b if s != 200 else "")
s, b = req("GET", "/api/my-farm", token=t1)
check("updated farm persisted", s == 200 and b.get("village") == "Ganeshpur" and b.get("farm_size") == 4.0,
      f"(got {s} {b.get('village')} {b.get('farm_size')})")

# Farmer isolation: user2 sees no farm
s, b = req("GET", "/api/my-farm", token=t2)
check("farmer isolation (user2 no farm)", s == 404, f"(got {s})")

# ================= P2: CROPS =================
print("== P2 CROPS ==")
s, b = req("POST", "/api/my-farm/crops",
           {"crop_name": "गेहूं", "season": "Rabi", "duration_days": 120, "water_requirement": "Medium"}, token=t1)
check("add crop", s == 200, b if s != 200 else "")
s, b = req("GET", "/api/my-farm/crops", token=t1)
check("list crops", s == 200 and len(b) == 1, f"(got {s} {len(b) if isinstance(b, list) else b})")
crop_id = b[0]["crop_id"]
s, b = req("PUT", f"/api/my-farm/crops/{crop_id}",
           {"crop_name": "गेहूं", "season": "Rabi", "duration_days": 140, "water_requirement": "Low"}, token=t1)
check("update crop", s == 200, b if s != 200 else "")
s, b = req("GET", "/api/my-farm/crops", token=t1)
check("updated crop persisted", s == 200 and b[0]["duration_days"] == 140, f"(got {s})")

# duplicate crop rejected
s, b = req("POST", "/api/my-farm/crops",
           {"crop_name": "गेहूं", "season": "Kharif", "duration_days": 90, "water_requirement": "High"}, token=t1)
check("duplicate crop rejected", s == 409, f"(got {s})")

# cross-user crop isolation
s, b = req("GET", "/api/my-farm/crops", token=t2)
check("crop isolation (user2 no crops)", s == 404, f"(got {s})")

# ================= P3: CROP STATUS =================
print("== P3 CROP STATUS ==")
s, b = req("POST", "/api/assistant", {"text": "मेरी फसल के क्या हाल हैं?"}, token=t1)
check("crop status OK", s == 200 and b.get("intent") == "CROP_STATUS" and b.get("status") == "OK",
      f"(got {s} {b.get('intent')} {b.get('status')})")
if isinstance(b, dict) and b.get("data"):
    d = b["data"]
    check("crop status has farm", d.get("farm", {}).get("village") == "Ganeshpur")
    check("crop status has crops", len(d.get("crops", [])) == 1)
    check("crop status weather present or unavailable",
          "weather" in d or d.get("weather_unavailable"))

# Missing-data honesty for user2
s, b = req("POST", "/api/assistant", {"text": "मेरी फसल के क्या हाल हैं?"}, token=t2)
check("crop status insufficient when no farm", s == 200 and b.get("status") == "INSUFFICIENT_DATA",
      f"(got {s} {b.get('status') if isinstance(b, dict) else b})")

# ================= P4: WEATHER =================
print("== P4 WEATHER ==")
import time
t0 = time.time()
s, b = req("GET", "/api/weather", token=t1)
t1_dur = time.time() - t0
check("weather fetch 200", s == 200, f"(got {s})")
check("weather has temp", isinstance(b, dict) and "temperature" in b, f"(got {b if not isinstance(b, dict) else list(b.keys())})")
# second fetch should be cache hit (fast)
t0 = time.time()
s, b2 = req("GET", "/api/weather", token=t1)
t2_dur = time.time() - t0
print(f"  weather timings: first={t1_dur:.2f}s second={t2_dur:.2f}s")

# ================= P5: DISEASE =================
print("== P5 DISEASE ==")
png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256
s, b = req("POST", "/api/disease-detection", token=t1,
           files={"file": ("leaf.png", png, "image/png")}, body={"crop_name": "Wheat"})
check("disease detection honest MODEL_NOT_CONFIGURED", s == 200 and b.get("status") == "MODEL_NOT_CONFIGURED",
      f"(got {s} {b.get('status') if isinstance(b, dict) else b})")

# Disease knowledge base
s, b = req("GET", "/api/diseases", token=t1)
check("disease knowledge list", s == 200 and isinstance(b, list), f"(got {s})")

# ================= PROFILE =================
print("== PROFILE ==")
s, b = req("GET", "/api/auth/me", token=t1)
check("profile me", s == 200 and b.get("username") == u1, f"(got {s})")

# ================= ASSISTANT WEATHER INTENT =================
print("== ASSISTANT OTHER INTENTS ==")
s, b = req("POST", "/api/assistant", {"text": "आज मौसम कैसा है?"}, token=t1)
check("weather intent", s == 200 and b.get("intent") == "WEATHER", f"(got {s} {b.get('intent') if isinstance(b, dict) else b})")
s, b = req("POST", "/api/assistant", {"text": "मेरा खेत कैसे देखूं?"}, token=t1)
check("my farm intent", s == 200 and b.get("intent") == "MY_FARM", f"(got {s} {b.get('intent') if isinstance(b, dict) else b})")

print()
print(f"TOTAL FAILS: {len(fails)}")
for f in fails:
    print("  FAIL:", f)
sys.exit(1 if fails else 0)