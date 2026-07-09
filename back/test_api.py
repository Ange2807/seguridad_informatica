## Prueba rápida contra proxy2: primero inicia sesión como staff y luego intenta crear un ticket.
import urllib.request, json
try:
    # Hace login de staff con el usuario de ejemplo 'sofia' y guarda el JWT devuelto.
    req = urllib.request.Request('http://localhost:4000/api/staff/login', data=b'{"username":"sofia","password":"Password123"}', headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    token = json.loads(resp.read())['token']
    print("Token sofia OK")
except Exception as e:
    # Si el login falla, imprime el error devuelto por la API o la excepción local.
    print("Login err:", getattr(e, 'read', lambda: b'')().decode() or e)

try:
    # Usa el token obtenido para intentar crear un ticket en Atención.
    req3 = urllib.request.Request('http://localhost:4000/api/atencion', data=b'{"cliente":"Test","asunto":"Test","estado":"abierto"}', headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    resp3 = urllib.request.urlopen(req3)
    print('Sofia ticket success:', resp3.read().decode())
except Exception as e:
    # Si la creación del ticket falla, imprime el detalle de la respuesta o la excepción.
    print('Sofia ticket error:', getattr(e, 'read', lambda: b'')().decode() or e)
