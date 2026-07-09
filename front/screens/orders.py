"""
Pantalla de Mis Pedidos.
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Header, Footer, DataTable
from textual.containers import Vertical, Horizontal


STATUS_STYLES = {
    "pendiente": "🟡 Pendiente",
    "enviado": "🟢 Enviado",
    "cancelado": "🔴 Cancelado",
}


class OrdersScreen(Screen):
    """Muestra las órdenes del usuario logueado."""

    BINDINGS = [
        ("ctrl+b", "go_catalog", "Catálogo"),
        ("ctrl+r", "refresh_orders", "Actualizar"),
        ("ctrl+l", "do_logout", "Cerrar Sesión"),
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Static("", id="user-info")
            yield Button("🛒 Catálogo", variant="default", id="btn-catalog", classes="nav-btn")
            yield Button("🔄 Actualizar", variant="default", id="btn-refresh", classes="nav-btn")
            yield Button("🚪 Salir", variant="error", id="btn-logout", classes="nav-btn")
        with Vertical(id="orders-wrapper"):
            yield Static("📋  Mis Pedidos", id="orders-title")
            yield DataTable(id="orders-table")
        yield Footer()

    async def on_mount(self) -> None:
        api = self.app.api
        display_name = api.nombre or api.username or "?"
        self.query_one("#user-info", Static).update(f"  👤 {display_name}  │  Rol: {api.role or ''}")

        table = self.query_one("#orders-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Estado", "Total", "Productos", "Fecha")
        await self._load_orders()

    async def _load_orders(self) -> None:
        table = self.query_one("#orders-table", DataTable)
        table.clear()
        try:
            orders = await self.app.api.get_my_orders()
            if not orders:
                table.add_row("—", "Sin pedidos", "—", "—", "—")
                return
            for o in orders:
                status = STATUS_STYLES.get(o.get("estado", ""), o.get("estado", "?"))
                total = f"${float(o.get('total', 0)):.2f}"
                items = o.get("items", [])
                productos = ", ".join(f"{it['producto']} x{it['cantidad']}" for it in items) if items else "—"
                fecha = str(o.get("creado_en", "—"))[:10]
                table.add_row(str(o["id"]), status, total, productos, fecha)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    # ── Actions ──────────────────────────────────────────

    def action_go_catalog(self) -> None:
        self.app.show_catalog()

    async def action_refresh_orders(self) -> None:
        await self._load_orders()

    def action_do_logout(self) -> None:
        self.app.do_logout()

    # ── Button events ────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "btn-catalog":
            self.app.show_catalog()
        elif btn == "btn-refresh":
            await self._load_orders()
        elif btn == "btn-logout":
            self.app.do_logout()
