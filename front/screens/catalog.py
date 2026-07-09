"""
Pantalla del Catálogo con carrito lateral.
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Static, Input, Button, Header, Footer, DataTable,
)
from textual.containers import Vertical, Horizontal, VerticalScroll


class CatalogScreen(Screen):
    """Muestra el catálogo de productos y un carrito lateral."""

    BINDINGS = [
        ("ctrl+a", "add_to_cart", "Añadir"),
        ("ctrl+o", "show_orders", "Mis Pedidos"),
        ("ctrl+l", "do_logout", "Cerrar Sesión"),
        ("ctrl+f", "focus_search", "Buscar"),
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Static("", id="user-info")
            yield Button("📋 Pedidos", variant="default", id="btn-orders", classes="nav-btn")
            yield Button("🚪 Salir", variant="error", id="btn-logout", classes="nav-btn")
        with Horizontal(id="catalog-layout"):
            with Vertical(id="product-panel"):
                with Horizontal(id="search-bar"):
                    yield Input(placeholder="Buscar producto…", id="search-input")
                    yield Button("🔍 Buscar", variant="primary", id="btn-search")
                yield DataTable(id="product-table")
            with Vertical(id="cart-panel"):
                yield Static("🛒  Carrito", id="cart-title")
                with VerticalScroll(id="cart-items-scroll"):
                    yield Static("Sin artículos", id="cart-empty")
                yield Static("Total: $0.00", id="cart-total")
                yield Button("✔ Finalizar Compra", variant="success", id="btn-checkout")
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────

    async def on_mount(self) -> None:
        # User info
        api = self.app.api
        display_name = api.nombre or api.username or "?"
        role_label = api.role or ""
        self.query_one("#user-info", Static).update(
            f"  👤 {display_name}  │  Rol: {role_label}"
        )

        # Setup table
        table = self.query_one("#product-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Producto", "Stock", "Precio")
        await self._load_catalog()

    async def _load_catalog(self, query: str = "") -> None:
        table = self.query_one("#product-table", DataTable)
        table.clear()
        try:
            items = await self.app.api.get_catalog(query)
            for item in items:
                table.add_row(
                    str(item["id"]),
                    item["producto"],
                    str(item["cantidad"]),
                    f"${float(item['precio']):.2f}",
                )
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    # ── Cart rendering ───────────────────────────────────

    def _refresh_cart(self) -> None:
        scroll = self.query_one("#cart-items-scroll", VerticalScroll)
        scroll.remove_children()

        cart = self.app.cart
        if not cart:
            scroll.mount(Static("Sin artículos", id="cart-empty"))
        else:
            for i, item in enumerate(cart):
                scroll.mount(
                    Static(
                        f"  {item['producto'][:18]:<18} x{item['cantidad']}  ${float(item['precio']) * item['cantidad']:.2f}",
                        classes="cart-item",
                    )
                )

        total = sum(float(it["precio"]) * it["cantidad"] for it in cart)
        self.query_one("#cart-total", Static).update(f"Total: ${total:.2f}")

    # ── Actions ──────────────────────────────────────────

    def action_add_to_cart(self) -> None:
        table = self.query_one("#product-table", DataTable)
        if table.cursor_row is None:
            self.notify("Selecciona un producto primero", severity="warning")
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_data = table.get_row(row_key)
        product_id = int(row_data[0])
        product_name = row_data[1]
        product_price = float(row_data[3].replace("$", ""))

        # Si el producto ya está en el carrito, incrementar cantidad
        for item in self.app.cart:
            if item["id"] == product_id:
                item["cantidad"] += 1
                self._refresh_cart()
                self.notify(f"+ {product_name}", severity="information")
                return

        self.app.cart.append({
            "id": product_id,
            "producto": product_name,
            "precio": product_price,
            "cantidad": 1,
        })
        self._refresh_cart()
        self.notify(f"+ {product_name}", severity="information")

    def action_show_orders(self) -> None:
        self.app.show_orders()

    def action_do_logout(self) -> None:
        self.app.do_logout()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    # ── Button events ────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id

        if btn == "btn-search":
            q = self.query_one("#search-input", Input).value.strip()
            await self._load_catalog(q)

        elif btn == "btn-checkout":
            cart = self.app.cart
            if not cart:
                self.notify("El carrito está vacío", severity="warning")
                return
            try:
                items_payload = [{"id": it["id"], "cantidad": it["cantidad"]} for it in cart]
                await self.app.api.checkout(items_payload)
                self.app.cart.clear()
                self._refresh_cart()
                await self._load_catalog()
                self.notify("✔ ¡Pedido procesado exitosamente!", severity="information")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif btn == "btn-orders":
            self.app.show_orders()

        elif btn == "btn-logout":
            self.app.do_logout()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            await self._load_catalog(event.value.strip())
