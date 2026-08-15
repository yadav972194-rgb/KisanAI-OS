import urllib.request, urllib.error, json, uuid, random
BASE='http://127.0.0.1:8712'
def req(method, path, body=None, token=None, form=False, files=None, timeout=30):
    url=BASE+path; data=None; headers={}
    if token: headers['Authorization']=f'Bearer {token}'
    if files is not None:
        boundary=uuid.uuid4().hex; buf=bytearray()
        for field,(fname,content,ctype) in files.items():
            buf+=f'--{boundary}\r\n'.encode(); buf+=f'Content-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'.encode(); buf+=f'Content-Type: {ctype}\r\n\r\n'.encode(); buf+=content+b'\r\n'
        if body is not None:
            for k,v in body.items():
                buf+=f'--{boundary}\r\n'.encode(); buf+=f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode(); buf+=str(v).encode()+b'\r\n'
        buf+=f'--{boundary}--\r\n'.encode(); data=bytes(buf); headers['Content-Type']=f'multipart/form-data; boundary={boundary}'
    elif body is not None:
        if form:
            data=urllib.parse.urlencode(body).encode(); headers['Content-Type']='application/x-www-form-urlencoded'
        else:
            data=json.dumps(body).encode(); headers['Content-Type']='application/json'
    r=urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp: return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw=e.read().decode()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {'raw': raw}
    except Exception as e: return None, {'error': str(e)}
u='diagdis'+str(random.randint(100000,999999))
req('POST','/api/auth/register',{'username':u,'password':'password123','full_name':'D','mobile':'9'+str(random.randint(100000000,999999999)),'role':'farmer'})
s,b=req('POST','/api/auth/token',{'username':u,'password':'password123'},form=True)
t=b['access_token']
png=b'\x89PNG\r\n\x1a\n'+b'\x00'*256
s,b=req('POST','/api/disease-detection',token=t,files={'file':('leaf.png',png,'image/png')},body={'crop_name':'Wheat'})
print('disease:',s,b)