"""
Cliente HTTP asíncrono para la API del proxy2.
"""
import os
import httpx

BASE_URL = os.environ.get("PROXY2_URL", "http://localhost:4000")


class ApiClient:
    """Gestiona la autenticación y las llamadas a la API."""

    def __init__(self):
        self.token: str | None = None
        self.username: str | None = None
        self.role: str | None = None
        self.nombre: str | None = None

    # ── Helpers ──────────────────────────────────────────

    # Arma la cabecera Authorization con el token guardado, si existe.
    def _auth_headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Guest auth ───────────────────────────────────────

    # Registra una cuenta de invitado nueva en proxy2.
    async def guest_register(self, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/guest/register", json={"username": username, "password": password})
            if r.status_code != 201:
                raise Exception(r.json().get("error", "Error al registrar"))
            return r.json()

    # Inicia sesión de invitado y guarda el token/rol en la instancia.
    async def guest_login(self, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/guest/login", json={"username": username, "password": password})
            if r.status_code != 200:
                raise Exception(r.json().get("error", "Credenciales inválidas"))
            data = r.json()
            self.token = data["token"]
            self.username = username
            self.role = "guest"
            return data

    # ── Staff auth ───────────────────────────────────────

    # Crea una cuenta interna vinculada a una cédula ya cargada por RRHH/Administrador.
    async def staff_register(self, cedula: str, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/staff/register", json={
                "cedula": cedula, "username": username, "password": password
            })
            if r.status_code != 201:
                raise Exception(r.json().get("error", "Error al registrar"))
            return r.json()

    # Inicia sesión de personal auto-registrado y guarda token/rol/nombre.
    async def staff_login(self, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/staff/login", json={"username": username, "password": password})
            if r.status_code != 200:
                raise Exception(r.json().get("error", "Credenciales inválidas"))
            data = r.json()
            self.token = data["token"]
            self.username = username
            self.role = data.get("role", "staff")
            self.nombre = data.get("nombre")
            return data

    # ── Catalog ──────────────────────────────────────────

    # Obtiene el catálogo público, opcionalmente filtrado por texto de búsqueda.
    async def get_catalog(self, query: str = ""):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            params = {"q": query} if query else {}
            r = await c.get("/api/public/catalog", params=params)
            if r.status_code != 200:
                raise Exception("No se pudo cargar el catálogo")
            return r.json()

    # ── Orders ───────────────────────────────────────────

    # Envía el carrito como pedido real; requiere sesión de invitado.
    async def checkout(self, items: list):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post(
                "/api/public/orders",
                json={"items": items},
                headers=self._auth_headers(),
            )
            if r.status_code != 201:
                raise Exception(r.json().get("error", "Error al procesar el pedido"))
            return r.json()

    # Devuelve el historial de pedidos del invitado autenticado.
    async def get_my_orders(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.get("/api/public/orders/mine", headers=self._auth_headers())
            if r.status_code != 200:
                raise Exception(r.json().get("error", "No se pudieron obtener los pedidos"))
            return r.json()

    # ── Session ──────────────────────────────────────────

    # Limpia el token y los datos de sesión guardados en la instancia.
    def logout(self):
        self.token = None
        self.username = None
        self.role = None
        self.nombre = None

    # ── Generic Department CRUD ──────────────────────────

    # Lista registros de un departamento (o pedidos), con búsqueda opcional.
    async def get_records(self, department: str, query: str = ""):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            params = {"q": query} if query else {}
            r = await c.get(f"/api/{department}", params=params, headers=self._auth_headers())
            if r.status_code != 200:
                raise Exception(r.json().get("error", f"Error al obtener {department}"))
            return r.json()

    # Crea un registro nuevo en el departamento indicado.
    async def create_record(self, department: str, data: dict):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post(
                f"/api/{department}",
                json=data,
                headers=self._auth_headers()
            )
            if r.status_code != 201:
                raise Exception(r.json().get("error", f"Error al crear en {department}"))
            return r.json()

    # Actualiza un registro existente del departamento por su id.
    async def update_record(self, department: str, record_id: int, data: dict):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.put(
                f"/api/{department}/{record_id}",
                json=data,
                headers=self._auth_headers()
            )
            if r.status_code != 200:
                raise Exception(r.json().get("error", f"Error al actualizar en {department}"))
            return r.json()

    # Elimina un registro del departamento por su id.
    async def delete_record(self, department: str, record_id: int):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.delete(
                f"/api/{department}/{record_id}",
                headers=self._auth_headers()
            )
            if r.status_code != 204:
                raise Exception(r.json().get("error", f"Error al eliminar en {department}"))
            return True
