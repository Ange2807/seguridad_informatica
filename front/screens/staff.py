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
    
    def __init__(self, department: str, title: str, id: str):
        super().__init__(id=id)
        self.department = department
        self.tab_title = title
        self.table_id = f"table-{department}"

    async def _load_data(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.clear()
        try:
            records = await self.app.api.get_records(self.department)
            self.populate_table(table, records)
        except Exception as e:
            self.app.notify(f"Error cargando {self.department}: {e}", severity="error")

    def populate_table(self, table: DataTable, records: list) -> None:
        pass


# ── Pestaña RRHH ─────────────────────────────────────────

class RrhhTab(BaseDeptTab):
    def __init__(self):
        super().__init__("rrhh", "👥 RRHH", "tab-rrhh")

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

    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Cédula", "Nombre", "Cargo")
        await self._load_data()

    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(str(r["id"]), r["cedula"], r["nombre"], r["cargo"])


# ── Pestaña Inventario ───────────────────────────────────

class InventarioTab(BaseDeptTab):
    def __init__(self):
        super().__init__("inventario", "📦 Inventario", "tab-inventario")

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.table_id, classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Producto", id="inv-producto", classes="form-input")
            yield Input(placeholder="Cantidad", id="inv-cantidad", type="integer", classes="form-input")
            yield Input(placeholder="Precio", id="inv-precio", type="number", classes="form-input")
            yield Input(placeholder="Ubicación", id="inv-ubicacion", classes="form-input")
        with Horizontal(classes="form-actions"):
            yield Button("Crear", variant="success", id="btn-inv-create")
            yield Button("Actualizar Sel.", variant="warning", id="btn-inv-update")
            yield Button("Eliminar Sel.", variant="error", id="btn-inv-delete")
            yield Button("Refrescar", variant="default", id="btn-inv-refresh")

    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Producto", "Cant.", "Precio", "Ubicación")
        await self._load_data()

    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(str(r["id"]), r["producto"], str(r["cantidad"]), f"${float(r['precio']):.2f}", r["ubicacion"])


# ── Pestaña Atención (Tickets) ───────────────────────────

class AtencionTab(BaseDeptTab):
    def __init__(self):
        super().__init__("atencion", "🎧 Tickets", "tab-atencion")

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.table_id, classes="dept-table")
        with Horizontal(classes="form-row"):
            yield Input(placeholder="Cliente", id="atn-cliente", classes="form-input")
            yield Input(placeholder="Asunto", id="atn-asunto", classes="form-input")
            yield Select(
                [("Abierto", "abierto"), ("En progreso", "en progreso"), ("Cerrado", "cerrado")],
                prompt="Estado...", id="atn-estado"
            )
        with Horizontal(classes="form-actions"):
            yield Button("Crear", variant="success", id="btn-atn-create")
            yield Button("Actualizar Sel.", variant="warning", id="btn-atn-update")
            yield Button("Eliminar Sel.", variant="error", id="btn-atn-delete")
            yield Button("Refrescar", variant="default", id="btn-atn-refresh")

    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Cliente", "Asunto", "Estado")
        await self._load_data()

    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(str(r["id"]), r["cliente"], r["asunto"], r["estado"])


# ── Pestaña Pedidos ──────────────────────────────────────

class PedidosTab(BaseDeptTab):
    def __init__(self):
        super().__init__("pedidos", "🛒 Pedidos", "tab-pedidos")

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

    async def on_mount(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Usuario", "Estado", "Total", "Fecha")
        await self._load_data()

    def populate_table(self, table: DataTable, records: list) -> None:
        for r in records:
            table.add_row(str(r["id"]), r["guest_username"], r["estado"], f"${float(r['total']):.2f}", str(r["creado_en"])[:10])


# ── Pantalla Principal del Staff ─────────────────────────

class StaffScreen(Screen):
    """Panel de control del Staff con pestañas dinámicas."""

    BINDINGS = [
        ("ctrl+l", "do_logout", "Cerrar Sesión"),
        ("ctrl+q", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Static("", id="user-info")
            yield Button("🚪 Salir", variant="error", id="btn-logout", classes="nav-btn")
        
        with Vertical(id="staff-wrapper"):
            yield TabbedContent(id="staff-tabs")
        yield Footer()

    async def on_mount(self) -> None:
        api = self.app.api
        display_name = api.nombre or api.username or "?"
        role = api.role or ""
        self.query_one("#user-info", Static).update(f"  👤 {display_name}  │  Rol: {role.upper()}")

        tabs = self.query_one("#staff-tabs", TabbedContent)
        
        if role in ["atencion", "administrador"]:
            await tabs.add_pane(TabPane("🎧 Tickets", AtencionTab()))
            await tabs.add_pane(TabPane("🛒 Pedidos", PedidosTab()))
        if role in ["inventario", "administrador"]:
            await tabs.add_pane(TabPane("📦 Inventario", InventarioTab()))
        if role in ["rrhh", "administrador"]:
            await tabs.add_pane(TabPane("👥 RRHH", RrhhTab()))

    # ── Utils ────────────────────────────────────────────

    def _get_selected_id(self, tab_instance: BaseDeptTab) -> int | None:
        table = tab_instance.query_one(f"#{tab_instance.table_id}", DataTable)
        if table.cursor_row is None:
            self.notify("Selecciona una fila primero", severity="warning")
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_data = table.get_row(row_key)
        return int(row_data[0])

    # ── Events ───────────────────────────────────────────

    def action_do_logout(self) -> None:
        self.app.do_logout()

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
                if not all(data.values()) or data["cargo"] == Select.BLANK:
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
                    if cargo != Select.BLANK: data["cargo"] = cargo
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
                data = {
                    "producto": tab.query_one("#inv-producto", Input).value.strip(),
                    "cantidad": tab.query_one("#inv-cantidad", Input).value.strip(),
                    "precio": tab.query_one("#inv-precio", Input).value.strip(),
                    "ubicacion": tab.query_one("#inv-ubicacion", Input).value.strip(),
                }
                if not all(data.values()):
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
                    if prod: data["producto"] = prod
                    if cant: data["cantidad"] = cant
                    if prec: data["precio"] = prec
                    if ubic: data["ubicacion"] = ubic
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

        # ATENCION
        elif btn.startswith("btn-atn-"):
            tab = self.query_one(AtencionTab)
            if btn == "btn-atn-refresh":
                await tab._load_data()
            elif btn == "btn-atn-create":
                data = {
                    "cliente": tab.query_one("#atn-cliente", Input).value.strip(),
                    "asunto": tab.query_one("#atn-asunto", Input).value.strip(),
                    "estado": tab.query_one("#atn-estado", Select).value,
                }
                if not data["cliente"] or not data["asunto"]:
                    self.notify("Falta cliente o asunto", severity="error")
                    return
                if data["estado"] == Select.BLANK:
                    data["estado"] = "abierto"
                try:
                    await self.app.api.create_record("atencion", data)
                    self.notify("Ticket creado")
                    await tab._load_data()
                except Exception as e:
                    self.notify(str(e), severity="error")
            elif btn == "btn-atn-update":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    data = {}
                    cli = tab.query_one("#atn-cliente", Input).value.strip()
                    asu = tab.query_one("#atn-asunto", Input).value.strip()
                    est = tab.query_one("#atn-estado", Select).value
                    if cli: data["cliente"] = cli
                    if asu: data["asunto"] = asu
                    if est != Select.BLANK: data["estado"] = est
                    try:
                        await self.app.api.update_record("atencion", rec_id, data)
                        self.notify("Ticket actualizado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")
            elif btn == "btn-atn-delete":
                rec_id = self._get_selected_id(tab)
                if rec_id:
                    try:
                        await self.app.api.delete_record("atencion", rec_id)
                        self.notify("Ticket eliminado")
                        await tab._load_data()
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
                    if est == Select.BLANK:
                        self.notify("Selecciona un estado", severity="error")
                        return
                    try:
                        await self.app.api.update_record("pedidos", rec_id, {"estado": est})
                        self.notify("Pedido actualizado")
                        await tab._load_data()
                    except Exception as e:
                        self.notify(str(e), severity="error")
