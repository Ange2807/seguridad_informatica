import urllib.request, json
try:
    req = urllib.request.Request('http://localhost:4000/api/staff/login', data=b'{"username":"sofia","password":"Password123"}', headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())['token']
    print("Token sofia OK")
except Exception as e:
    print("Login err:", getattr(e, 'read', lambda: b'')().decode() or e)

try:
    # We don't know the admin username, let's just test with sofia first
    req3 = urllib.request.Request('http://localhost:4000/api/atencion', data=b'{"cliente":"Test","asunto":"Test","estado":"abierto"}', headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    resp3 = urllib.request.urlopen(req3)
    print('Sofia ticket success:', resp3.read().decode())
except Exception as e:
    print('Sofia ticket error:', getattr(e, 'read', lambda: b'')().decode() or e)
