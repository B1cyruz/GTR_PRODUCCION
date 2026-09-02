import requests

tests = [
    ('admin', 'Admin123*'),
    ('admin@gtrlogistics.com', 'Admin123*'),
    ('coordinador', 'Coord123*'),
    ('coordinacion@gtrlogistics.com', 'Coord123*'),
    ('repartidor1', 'Driver123*'),
    ('jose.martinez@gtrlogistics.com', 'Driver123*'),
    ('repartidor2', 'Driver123*'),
    ('sergio.salgado@gtrlogistics.com', 'Driver123*'),
    ('repartidor3', 'Driver123*'),
    ('juan.espinosa@gtrlogistics.com', 'Driver123*'),
    ('repartidor4', 'Driver123*'),
    ('juan.amazan@gtrlogistics.com', 'Driver123*'),
]

print("=== PROBANDO AUTENTICACIÓN EN LOGIN ===")
for user, pwd in tests:
    res = requests.post(
        'http://127.0.0.1:8000/api/auth/login/',
        json={'email_or_user': user, 'password': pwd}
    )
    data = res.json()
    status = "OK [200]" if res.status_code == 200 and data.get("success") else f"FAIL [{res.status_code}]"
    print(f"[{status}] Usuario: {user:<32} -> Rol: {data.get('role')} | Redirección: {data.get('redirect_url')}")

print("\n=== PROBANDO BOTONES 1-CLIC (PROVIDER LOGIN) ===")
for role_key in ['admin', 'coordinador', 'repartidor1', 'repartidor2', 'google', 'outlook', 'corporate']:
    res = requests.post(
        'http://127.0.0.1:8000/api/auth/provider-login/',
        json={'provider': role_key}
    )
    data = res.json()
    status = "OK [200]" if res.status_code == 200 and data.get("success") else f"FAIL [{res.status_code}]"
    print(f"[{status}] Provider: {role_key:<20} -> Mensaje: {data.get('message')} | Redir: {data.get('redirect_url')}")
