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

    def _auth_headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Guest auth ───────────────────────────────────────

    async def guest_register(self, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/guest/register", json={"username": username, "password": password})
            if r.status_code != 201:
                raise Exception(r.json().get("error", "Error al registrar"))
            return r.json()

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

    async def staff_register(self, cedula: str, username: str, password: str):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.post("/api/staff/register", json={
                "cedula": cedula, "username": username, "password": password
            })
            if r.status_code != 201:
                raise Exception(r.json().get("error", "Error al registrar"))
            return r.json()

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

    async def get_catalog(self, query: str = ""):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            params = {"q": query} if query else {}
            r = await c.get("/api/public/catalog", params=params)
            if r.status_code != 200:
                raise Exception("No se pudo cargar el catálogo")
            return r.json()

    # ── Orders ───────────────────────────────────────────

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

    async def get_my_orders(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
            r = await c.get("/api/public/orders/mine", headers=self._auth_headers())
            if r.status_code != 200:
                raise Exception(r.json().get("error", "No se pudieron obtener los pedidos"))
            return r.json()

    # ── Session ──────────────────────────────────────────

    def logout(self):
        self.token = None
        self.username = None
        self.role = None
        self.nombre = None
