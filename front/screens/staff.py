"""
Pantalla de Staff con pestañas según el rol.
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Static, Input, Button, Header, Footer, DataTable,
    TabbedContent, TabPane, Select
)
from textual.containers import Vertical, Horizontal


class BaseDeptTab(Vertical):
    """Clase base para las pestañas de departamento."""
    
    # Guarda el departamento, el título de la pestaña y el id de su tabla.
    def __init__(self, department: str, title: str, id: str):
        super().__init__(id=id)
        self.department = department
        self.tab_title = title
        self.table_id = f"table-{department}"

    # Descarga los registros del departamento y repuebla la tabla.
    async def _load_data(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.clear()
        try:
            records = await self.app.api.get_records(self.department)
            self.populate_table(table, records)
        except Exception as e:
            self.app.notify(f"Error cargando {self.department}: {e}", severity="error")

    # Pinta las filas en la tabla; cada subclase define sus columnas.
    def populate_table(self, table: DataTable, records: list) -> None:
        pass

    # Rellena el formulario con la fila seleccionada; cada subclase lo implementa.
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        pass


# ── Pestaña RRHH ─────────────────────────────────────────

class RrhhTab(BaseDeptTab):
    # Fija el departamento "rrhh" para esta pestaña.
    def __init__(self):
        super().__init__("rrhh", "👥 RRHH", "tab-rrhh")

    # Dibuja la tabla de empleados y el formulario de cédula/nombre/cargo.
    def compose(self) -> ComposeResult:
        yield DataTable(id=self.table_id, classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Cédula", id="rrhh-cedula", classes="form-input")
            yield Input(placeholder="Nombre", id="rrhh-nombre", classes="form-input")
            yield Select(
                [("Atención", "atencion"), ("RRHH", "rrhh"), ("Inventario", "inventario"), ("Administrador", "administrador")],
                prompt="Cargo...", id="rrhh-cargo"
            )
        with Horizontal(classes="form-actions"):
            yield Button("Crear", variant="success", id="btn-rrhh-create")
            yield Button("Actualizar Sel.", variant="warning", id="btn-rrhh-update")
            yield Button("Refrescar", variant="default", id="btn-rrhh-refresh")

    # Configura columnas de la tabla y carga los empleados al montar.
    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Cédula", "Nombre", "Cargo")
        await self._load_data()

    # Agrega una fila por cada empleado recibido de la API.
    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(str(r["id"]), r["cedula"], r["nombre"], r["cargo"])

    # Copia la fila seleccionada al formulario para poder editarla.
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.control.id == self.table_id:
            row = event.control.get_row(event.row_key)
            self.query_one("#rrhh-cedula", Input).value = str(row[1])
            self.query_one("#rrhh-nombre", Input).value = str(row[2])
            # For Select, value might not match exactly if casing is different, but we try:
            cargo = str(row[3]).lower()
            try:
                self.query_one("#rrhh-cargo", Select).value = cargo
            except:
                pass


# ── Pestaña Inventario ───────────────────────────────────

class InventarioTab(BaseDeptTab):
    # Fija el departamento "inventario" para esta pestaña.
    def __init__(self):
        super().__init__("inventario", "📦 Inventario", "tab-inventario")

    # Dibuja la tabla de productos y el formulario de producto/cantidad/precio/ubicación/disponibilidad.
    def compose(self) -> ComposeResult:
        yield DataTable(id=self.table_id, classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Producto", id="inv-producto", classes="form-input")
            yield Input(placeholder="Cantidad", id="inv-cantidad", type="integer", classes="form-input")
            yield Input(placeholder="Precio", id="inv-precio", type="number", classes="form-input")
            yield Input(placeholder="Ubicación", id="inv-ubicacion", classes="form-input")
            yield Select(
                [("Disponible", True), ("No disponible", False)],
                value=True, allow_blank=False, id="inv-disponible"
            )
        with Horizontal(classes="form-actions"):
            yield Button("Crear", variant="success", id="btn-inv-create")
            yield Button("Actualizar Sel.", variant="warning", id="btn-inv-update")
            yield Button("Eliminar Sel.", variant="error", id="btn-inv-delete")
            yield Button("Refrescar", variant="default", id="btn-inv-refresh")

    # Configura columnas de la tabla y carga el inventario al montar.
    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Producto", "Cant.", "Precio", "Ubicación", "Disponible")
        await self._load_data()

    # Agrega una fila por cada producto recibido de la API.
    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            disponible = "Sí" if r.get("disponible", True) else "No"
            table.add_row(
                str(r["id"]), r["producto"], str(r["cantidad"]),
                f"${float(r['precio']):.2f}", r["ubicacion"], disponible,
            )

    # Copia la fila seleccionada al formulario para poder editarla.
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.control.id == self.table_id:
            row = event.control.get_row(event.row_key)
            self.query_one("#inv-producto", Input).value = str(row[1])
            self.query_one("#inv-cantidad", Input).value = str(row[2])
            self.query_one("#inv-precio", Input).value = str(row[3]).replace("$", "")
            self.query_one("#inv-ubicacion", Input).value = str(row[4])
            try:
                self.query_one("#inv-disponible", Select).value = (str(row[5]) == "Sí")
            except Exception:
                pass


# ── Pestaña Atención (Nuevo Pedido) ──────────────────────

class NuevoPedidoTab(Vertical):
    """Atención arma un pedido del catálogo a nombre de un comprador sin cuenta
    (solo selección de productos + nombre/cédula, sin cobro)."""

    def __init__(self):
        super().__init__(id="tab-nuevo-pedido")
        self.catalog: list = []
        self.cart: list = []

    # Dibuja el catálogo, el formulario de cantidad/agregar y el pedido en construcción.
    def compose(self) -> ComposeResult:
        yield Static("Catálogo — selecciona un producto")
        yield DataTable(id="table-np-catalogo", classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Cantidad", id="np-cantidad", type="integer", classes="form-input")
            yield Button("Agregar al pedido", variant="success", id="btn-np-agregar")
            yield Button("Refrescar catálogo", variant="default", id="btn-np-refrescar")

        yield Static("Pedido actual")
        yield DataTable(id="table-np-carrito", classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Nombre del comprador", id="np-nombre", classes="form-input")
            yield Input(placeholder="Cédula del comprador", id="np-cedula", classes="form-input")
        with Horizontal(classes="form-actions"):
            yield Button("Quitar Sel. del pedido", variant="warning", id="btn-np-quitar")
            yield Button("Confirmar Pedido", variant="success", id="btn-np-confirmar")

    # Configura columnas de ambas tablas y carga el catálogo al montar.
    async def on_mount(self) -> None:
        catalog_table = self.query_one("#table-np-catalogo", DataTable)
        catalog_table.cursor_type = "row"
        catalog_table.add_columns("ID", "Producto", "Precio", "Disponibles")

        cart_table = self.query_one("#table-np-carrito", DataTable)
        cart_table.cursor_type = "row"
        cart_table.add_columns("Producto", "Cantidad", "Subtotal")

        await self.load_catalog()

    # Descarga el catálogo público (mismo que ve el cliente) y repuebla la tabla.
    async def load_catalog(self) -> None:
        table = self.query_one("#table-np-catalogo", DataTable)
        table.clear()
        try:
            self.catalog = await self.app.api.get_catalog()
        except Exception as e:
            self.app.notify(f"Error cargando catálogo: {e}", severity="error")
            return
        for p in self.catalog:
            table.add_row(str(p["id"]), p["producto"], f"${float(p['precio']):.2f}", str(p["cantidad"]))

    # Devuelve el producto de catálogo actualmente seleccionado, o None.
    def selected_product(self):
        table = self.query_one("#table-np-catalogo", DataTable)
        if table.cursor_row is None or table.cursor_row < 0 or table.cursor_row >= len(self.catalog):
            return None
        return self.catalog[table.cursor_row]

    # Redibuja la tabla del pedido en construcción a partir del carrito en memoria.
    def render_cart(self) -> None:
        table = self.query_one("#table-np-carrito", DataTable)
        table.clear()
        for item in self.cart:
            subtotal = item["precio"] * item["cantidad"]
            table.add_row(item["producto"], str(item["cantidad"]), f"${subtotal:.2f}")

    # Agrega un producto al pedido en memoria, o suma cantidad si ya estaba.
    def add_to_cart(self, product: dict, cantidad: int) -> None:
        existing = next((i for i in self.cart if i["id"] == product["id"]), None)
        if existing:
            existing["cantidad"] += cantidad
        else:
            self.cart.append({
                "id": product["id"],
                "producto": product["producto"],
                "precio": float(product["precio"]),
                "cantidad": cantidad,
            })
        self.render_cart()

    # Quita del pedido el item seleccionado en la tabla del carrito.
    def remove_selected_from_cart(self) -> bool:
        table = self.query_one("#table-np-carrito", DataTable)
        if table.cursor_row is None or table.cursor_row < 0 or table.cursor_row >= len(self.cart):
            return False
        self.cart.pop(table.cursor_row)
        self.render_cart()
        return True

    # Vacía el pedido y limpia el formulario tras confirmar (o cancelar) la compra.
    def reset(self) -> None:
        self.cart = []
        self.render_cart()
        self.query_one("#np-nombre", Input).value = ""
        self.query_one("#np-cedula", Input).value = ""
        self.query_one("#np-cantidad", Input).value = ""


# ── Pestaña Pedidos ──────────────────────────────────────

class PedidosTab(BaseDeptTab):
    # Fija el departamento "pedidos" para esta pestaña.
    def __init__(self):
        super().__init__("pedidos", "🛒 Pedidos", "tab-pedidos")

    # Dibuja la tabla de pedidos y el selector de nuevo estado.
    def compose(self) -> ComposeResult:
        yield DataTable(id=self.table_id, classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Select(
                [("Pendiente", "pendiente"), ("Enviado", "enviado"), ("Cancelado", "cancelado")],
                prompt="Nuevo Estado...", id="ped-estado"
            )
        with Horizontal(classes="form-actions"):
            yield Button("Actualizar Estado Sel.", variant="warning", id="btn-ped-update")
            yield Button("Refrescar", variant="default", id="btn-ped-refresh")

    # Configura columnas de la tabla y carga los pedidos al montar.
    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Comprador", "Cédula", "Estado", "Total", "Fecha")
        await self._load_data()

    # Agrega una fila por cada pedido recibido de la API (invitado o creado por Atención).
    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(
                str(r["id"]), r.get("comprador") or "", r.get("cliente_cedula") or "-",
                r["estado"], f"${float(r['total']):.2f}", str(r["creado_en"])[:10],
            )

    # Copia el estado del pedido seleccionado al selector para poder cambiarlo.
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.control.id == self.table_id:
            row = event.control.get_row(event.row_key)
            estado = str(row[3]).lower()
            try:
                self.query_one("#ped-estado", Select).value = estado
            except:
                pass


# ── Pantalla Principal del Staff ─────────────────────────

class StaffScreen(Screen):
    """Panel de control del Staff con pestañas dinámicas."""

    BINDINGS = [
        ("ctrl+l", "do_logout", "Cerrar Sesión"),
        ("ctrl+q", "quit", "Salir"),
    ]

    # Dibuja la barra superior (usuario + salir) y el contenedor de pestañas.
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Static("", id="user-info")
            yield Button("🚪 Salir", variant="error", id="btn-logout", classes="nav-btn")

        with Vertical(id="staff-wrapper"):
            yield TabbedContent(id="staff-tabs")
        yield Footer()

    # Muestra el usuario/rol actual y agrega solo las pestañas que su rol puede ver.
    async def on_mount(self) -> None:
        api = self.app.api
        display_name = api.nombre or api.username or "?"
        role = api.role or ""
        self.query_one("#user-info", Static).update(f"  👤 {display_name}  │  Rol: {role.upper()}")

        tabs = self.query_one("#staff-tabs", TabbedContent)
        
        if role in ["atencion", "administrador"]:
            await tabs.add_pane(TabPane("🛍️ Nuevo Pedido", NuevoPedidoTab()))
            await tabs.add_pane(TabPane("🛒 Pedidos", PedidosTab()))
        if role in ["inventario", "administrador"]:
            await tabs.add_pane(TabPane("📦 Inventario", InventarioTab()))
        if role in ["rrhh", "administrador"]:
            await tabs.add_pane(TabPane("👥 RRHH", RrhhTab()))

    # ── Utils ────────────────────────────────────────────

    # Devuelve el id de la fila seleccionada en la tabla de la pestaña, o None si no hay selección.
    def _get_selected_id(self, tab_instance: BaseDeptTab) -> int | None:
        table = tab_instance.query_one(f"#{tab_instance.table_id}", DataTable)
        if table.cursor_row is None:
            self.notify("Selecciona una fila primero", severity="warning")
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_data = table.get_row(row_key)
        return int(row_data[0])

    # ── Events ───────────────────────────────────────────

    # Delega el cierre de sesión a la app principal.
    def action_do_logout(self) -> None:
        self.app.do_logout()

    # Enruta cada botón presionado (por prefijo de id) al CRUD de su departamento.
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "btn-logout":
            self.action_do_logout()
            return
        
        # RRHH
        if btn.startswith("btn-rrhh-"):
            tab = self.query_one(RrhhTab)
            if btn == "btn-rrhh-refresh":
                await tab._load_data()
            elif btn == "btn-rrhh-create":
                data = {
                    "cedula": tab.query_one("#rrhh-cedula", Input).value.strip(),
                    "nombre": tab.query_one("#rrhh-nombre", Input).value.strip(),
                    "cargo": tab.query_one("#rrhh-cargo", Select).value,
                }
                if not all([data["cedula"], data["nombre"]]) or not isinstance(data["cargo"], str):
                    self.notify("Faltan campos", severity="error")
                    return
                try:
                    await self.app.api.create_record("rrhh", data)
                    self.notify("Empleado creado")
                    await tab._load_data()
                except Exception as e:
                    self.notify(str(e), severity="error")
            elif btn == "btn-rrhh-update":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    data = {}
                    nombre = tab.query_one("#rrhh-nombre", Input).value.strip()
                    cargo = tab.query_one("#rrhh-cargo", Select).value
                    if nombre: data["nombre"] = nombre
                    if isinstance(cargo, str): data["cargo"] = cargo
                    try:
                        await self.app.api.update_record("rrhh", rec_id, data)
                        self.notify("Empleado actualizado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")

        # INVENTARIO
        elif btn.startswith("btn-inv-"):
            tab = self.query_one(InventarioTab)
            if btn == "btn-inv-refresh":
                await tab._load_data()
            elif btn == "btn-inv-create":
                disponible = tab.query_one("#inv-disponible", Select).value
                data = {
                    "producto": tab.query_one("#inv-producto", Input).value.strip(),
                    "cantidad": tab.query_one("#inv-cantidad", Input).value.strip(),
                    "precio": tab.query_one("#inv-precio", Input).value.strip(),
                    "ubicacion": tab.query_one("#inv-ubicacion", Input).value.strip(),
                    "disponible": disponible if isinstance(disponible, bool) else True,
                }
                if not all([data["producto"], data["cantidad"], data["precio"], data["ubicacion"]]):
                    self.notify("Faltan campos", severity="error")
                    return
                try:
                    await self.app.api.create_record("inventario", data)
                    self.notify("Producto creado")
                    await tab._load_data()
                except Exception as e:
                    self.notify(str(e), severity="error")
            elif btn == "btn-inv-update":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    data = {}
                    prod = tab.query_one("#inv-producto", Input).value.strip()
                    cant = tab.query_one("#inv-cantidad", Input).value.strip()
                    prec = tab.query_one("#inv-precio", Input).value.strip()
                    ubic = tab.query_one("#inv-ubicacion", Input).value.strip()
                    disp = tab.query_one("#inv-disponible", Select).value
                    if prod: data["producto"] = prod
                    if cant: data["cantidad"] = cant
                    if prec: data["precio"] = prec
                    if ubic: data["ubicacion"] = ubic
                    if isinstance(disp, bool): data["disponible"] = disp
                    try:
                        await self.app.api.update_record("inventario", rec_id, data)
                        self.notify("Producto actualizado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")
            elif btn == "btn-inv-delete":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    try:
                        await self.app.api.delete_record("inventario", rec_id)
                        self.notify("Producto eliminado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")

        # NUEVO PEDIDO (Atención)
        elif btn.startswith("btn-np-"):
            tab = self.query_one(NuevoPedidoTab)
            if btn == "btn-np-refrescar":
                await tab.load_catalog()
            elif btn == "btn-np-agregar":
                product = tab.selected_product()
                if not product:
                    self.notify("Selecciona un producto del catálogo", severity="warning")
                    return
                cant_raw = tab.query_one("#np-cantidad", Input).value.strip()
                if not cant_raw.isdigit() or int(cant_raw) <= 0:
                    self.notify("Ingresa una cantidad válida", severity="error")
                    return
                tab.add_to_cart(product, int(cant_raw))
                tab.query_one("#np-cantidad", Input).value = ""
            elif btn == "btn-np-quitar":
                if not tab.remove_selected_from_cart():
                    self.notify("Selecciona un producto del pedido primero", severity="warning")
            elif btn == "btn-np-confirmar":
                nombre = tab.query_one("#np-nombre", Input).value.strip()
                cedula = tab.query_one("#np-cedula", Input).value.strip()
                if not nombre or not cedula:
                    self.notify("Falta el nombre o la cédula del comprador", severity="error")
                    return
                if not tab.cart:
                    self.notify("El pedido no tiene productos", severity="error")
                    return
                items = [{"id": i["id"], "cantidad": i["cantidad"]} for i in tab.cart]
                try:
                    order = await self.app.api.create_record(
                        "pedidos",
                        {"cliente_nombre": nombre, "cliente_cedula": cedula, "items": items},
                    )
                    self.notify(f"Pedido #{order['id']} creado — ${float(order['total']):.2f}")
                    tab.reset()
                    await tab.load_catalog()
                    try:
                        await self.query_one(PedidosTab)._load_data()
                    except Exception:
                        pass
                except Exception as e:
                    self.notify(str(e), severity="error")

        # PEDIDOS
        elif btn.startswith("btn-ped-"):
            tab = self.query_one(PedidosTab)
            if btn == "btn-ped-refresh":
                await tab._load_data()
            elif btn == "btn-ped-update":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    est = tab.query_one("#ped-estado", Select).value
                    if not isinstance(est, str):
                        self.notify("Selecciona un estado", severity="error")
                        return
                    try:
                        await self.app.api.update_record("pedidos", rec_id, {"estado": est})
                        self.notify("Pedido actualizado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")
