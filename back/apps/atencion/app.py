import os

import httpx
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

PROXY2_URL = os.environ.get("PROXY2_URL", "http://proxy2:4000")
DEPARTMENT = os.environ.get("DEPARTMENT", "atencion")
TITLE = "Atención al Cliente"
TICKET_FIELDS = [
    ("cliente", "Cliente"),
    ("asunto", "Asunto"),
    ("estado", "Estado"),
]
ORDER_STATUSES = ["pendiente", "procesando", "enviado", "entregado", "cancelado"]


class TicketModal(ModalScreen):
    CSS = """
    TicketModal { align: center middle; }
    #form-box { width: 54; border: round $accent; padding: 1 2; background: $surface; }
    #form-box Input { margin-bottom: 1; }
    """

    def __init__(self, form_title, initial=None):
        super().__init__()
        self.form_title = form_title
        self.initial = initial or {}

    def compose(self) -> ComposeResult:
        with Vertical(id="form-box"):
            yield Label(self.form_title)
            for key, label in TICKET_FIELDS:
                yield Input(value=str(self.initial.get(key, "")), placeholder=label, id=f"field-{key}")
            with Horizontal():
                yield Button("Guardar", id="save", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        data = {key: self.query_one(f"#field-{key}", Input).value for key, _ in TICKET_FIELDS}
        self.dismiss(data)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class ConfirmModal(ModalScreen):
    CSS = """
    ConfirmModal { align: center middle; }
    #confirm-box { width: 46; border: round $error; padding: 1 2; background: $surface; }
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self.message)
            with Horizontal():
                yield Button("Eliminar", id="yes", variant="error")
                yield Button("Cancelar", id="no")

    @on(Button.Pressed, "#yes")
    def yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def no(self) -> None:
        self.dismiss(False)


class OrderStatusModal(ModalScreen):
    CSS = """
    OrderStatusModal { align: center middle; }
    #status-box { width: 46; border: round $accent; padding: 1 2; background: $surface; }
    """

    def __init__(self, order_id, current_status):
        super().__init__()
        self.order_id = order_id
        self.current_status = current_status

    def compose(self) -> ComposeResult:
        with Vertical(id="status-box"):
            yield Label(f"Pedido #{self.order_id} — cambiar estado")
            yield Select(
                [(status, status) for status in ORDER_STATUSES],
                value=self.current_status if self.current_status in ORDER_STATUSES else ORDER_STATUSES[0],
                id="status-select",
            )
            with Horizontal():
                yield Button("Guardar", id="save", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        self.dismiss(self.query_one("#status-select", Select).value)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class RegisterModal(ModalScreen):
    CSS = """
    RegisterModal { align: center middle; }
    #register-box { width: 58; border: round $accent; padding: 1 2; background: $surface; }
    #register-box Input { margin-bottom: 1; }
    #register-hint { color: $text-muted; margin-bottom: 1; }
    #register-status { height: 1; color: $error; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="register-box"):
            yield Label("Registro de nuevo usuario")
            yield Label(
                "Tu cédula debe existir en la tabla de empleados (la carga RRHH o Administrador).",
                id="register-hint",
            )
            yield Input(placeholder="cédula", id="reg-cedula")
            yield Input(placeholder="usuario deseado", id="reg-username")
            yield Input(placeholder="contraseña", password=True, id="reg-password")
            yield Static("", id="register-status")
            with Horizontal():
                yield Button("Registrarme", id="submit", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

    @on(Button.Pressed, "#submit")
    async def submit(self) -> None:
        cedula = self.query_one("#reg-cedula", Input).value
        username = self.query_one("#reg-username", Input).value
        password = self.query_one("#reg-password", Input).value
        status = self.query_one("#register-status", Static)
        if not cedula or not username or not password:
            status.update("Completa cédula, usuario y contraseña.")
            return
        status.update("Registrando...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(
                    f"{PROXY2_URL}/api/staff/register",
                    json={"cedula": cedula, "username": username, "password": password},
                )
                data = res.json()
                if res.status_code >= 400:
                    status.update(f"Error: {data.get('error', 'no se pudo registrar')}")
                    return
        except httpx.HTTPError as exc:
            status.update(f"Error de red: {exc}")
            return
        self.dismiss({"username": username, "cargo": data.get("cargo")})

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class DepartmentApp(App):
    CSS = """
    Screen { align: center middle; }
    #login-box { width: 54; border: round $accent; padding: 1 2; }
    #status { height: 1; color: $error; }
    #main { width: 1fr; height: 1fr; padding: 1 2; }
    Input.search-box { width: 1fr; margin-bottom: 1; }
    DataTable { height: 1fr; width: 1fr; }
    """

    BINDINGS = [
        ("n", "new_record", "Nuevo (tickets)"),
        ("e", "edit_record", "Editar"),
        ("d", "delete_record", "Eliminar (tickets)"),
        ("r", "refresh", "Refrescar"),
    ]

    def __init__(self):
        super().__init__()
        self.token = None
        self.current_tickets = []
        self.current_pedidos = []

    def compose(self) -> ComposeResult:
        yield Header(name=TITLE)
        with Vertical(id="login-box"):
            yield Label(f"{TITLE} — inicio de sesión")
            yield Input(placeholder="usuario", id="username")
            yield Input(placeholder="contraseña", password=True, id="password")
            with Horizontal():
                yield Button("Iniciar sesión", id="login-btn", variant="success")
                yield Button("Registrarme", id="register-btn")
            yield Static("", id="status")
        yield Footer()

    @on(Button.Pressed, "#login-btn")
    async def login_button_pressed(self) -> None:
        await self.handle_login()

    @on(Button.Pressed, "#register-btn")
    def open_register(self) -> None:
        def handle_result(result):
            if result:
                self.query_one("#username", Input).value = result["username"]
                self.query_one("#status", Static).update(
                    f"Cuenta creada (cargo: {result.get('cargo')}). Ya puedes iniciar sesión."
                )

        self.push_screen(RegisterModal(), handle_result)

    def on_mount(self) -> None:
        self.title = TITLE
        self.query_one("#username", Input).focus()

    @on(Input.Submitted, "#username")
    def focus_password(self) -> None:
        self.query_one("#password", Input).focus()

    @on(Input.Submitted, "#password")
    async def handle_login(self) -> None:
        username = self.query_one("#username", Input).value
        password = self.query_one("#password", Input).value
        status = self.query_one("#status", Static)
        status.update("Autenticando...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                login_res = await client.post(
                    f"{PROXY2_URL}/auth/login",
                    json={"username": username, "password": password},
                )
                login_data = login_res.json()
                if login_res.status_code != 200:
                    staff_res = await client.post(
                        f"{PROXY2_URL}/api/staff/login",
                        json={"username": username, "password": password},
                    )
                    login_data = staff_res.json()
                    if staff_res.status_code != 200:
                        status.update(f"Error: {login_data.get('error', 'credenciales inválidas')}")
                        return
                self.token = login_data["token"]
        except httpx.HTTPError as exc:
            status.update(f"Error de red: {exc}")
            return
        await self.show_main()

    async def show_main(self) -> None:
        await self.query_one("#login-box").remove()
        main = Vertical(id="main")
        await self.mount(main)
        with_tabs = TabbedContent()
        await main.mount(with_tabs)
        await with_tabs.add_pane(
            TabPane("Tickets", Input(placeholder="Buscar... (Enter)", id="search-tickets", classes="search-box"), DataTable(id="table-tickets"), id="tab-tickets")
        )
        await with_tabs.add_pane(
            TabPane("Pedidos", Input(placeholder="Buscar... (Enter)", id="search-pedidos", classes="search-box"), DataTable(id="table-pedidos"), id="tab-pedidos")
        )
        self.query_one("#table-tickets", DataTable).cursor_type = "row"
        self.query_one("#table-pedidos", DataTable).cursor_type = "row"
        await self.load_tickets()
        await self.load_pedidos()
        self.query_one("#search-tickets", Input).focus()

    @on(Input.Submitted, "#search-tickets")
    async def on_search_tickets(self) -> None:
        await self.load_tickets()

    @on(Input.Submitted, "#search-pedidos")
    async def on_search_pedidos(self) -> None:
        await self.load_pedidos()

    def active_tab(self) -> str:
        return self.query_one(TabbedContent).active

    async def action_refresh(self) -> None:
        if not self.token:
            return
        if self.active_tab() == "tab-pedidos":
            self.query_one("#search-pedidos", Input).value = ""
            await self.load_pedidos()
        else:
            self.query_one("#search-tickets", Input).value = ""
            await self.load_tickets()

    async def load_tickets(self) -> None:
        if not self.token:
            return
        query = self.query_one("#search-tickets", Input).value
        params = {"q": query} if query else {}
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{PROXY2_URL}/api/{DEPARTMENT}",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
            )
            rows = res.json()
        table = self.query_one("#table-tickets", DataTable)
        table.clear(columns=True)
        self.current_tickets = rows if isinstance(rows, list) else []
        columns = [key for key, _ in TICKET_FIELDS]
        table.add_columns("id", *columns)
        if self.current_tickets:
            for row in self.current_tickets:
                table.add_row(str(row["id"]), *[str(row.get(c, "")) for c in columns])
        else:
            table.add_row("-", *["sin registros" for _ in columns])

    async def load_pedidos(self) -> None:
        if not self.token:
            return
        query = self.query_one("#search-pedidos", Input).value
        params = {"q": query} if query else {}
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{PROXY2_URL}/api/pedidos",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
            )
            rows = res.json()
        table = self.query_one("#table-pedidos", DataTable)
        table.clear(columns=True)
        self.current_pedidos = rows if isinstance(rows, list) else []
        table.add_columns("id", "cliente", "total", "estado", "fecha", "items")
        if self.current_pedidos:
            for row in self.current_pedidos:
                items_summary = ", ".join(
                    f"{item['cantidad']}x {item['producto']}" for item in row.get("items", [])
                )
                table.add_row(
                    str(row["id"]),
                    row.get("guest_username", ""),
                    str(row.get("total", "")),
                    row.get("estado", ""),
                    str(row.get("creado_en", ""))[:19],
                    items_summary,
                )
        else:
            table.add_row("-", "sin pedidos", "", "", "", "")

    def selected_ticket(self):
        table = self.query_one("#table-tickets", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self.current_tickets):
            return None
        return self.current_tickets[table.cursor_row]

    def selected_pedido(self):
        table = self.query_one("#table-pedidos", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self.current_pedidos):
            return None
        return self.current_pedidos[table.cursor_row]

    def action_new_record(self) -> None:
        if not self.token:
            return
        if self.active_tab() == "tab-pedidos":
            self.notify("Los pedidos no se crean manualmente, solo desde el checkout", severity="warning")
            return

        def handle_result(data):
            if data:
                self.run_worker(self.submit_new_ticket(data))

        self.push_screen(TicketModal(f"Nuevo — {TITLE}"), handle_result)

    async def submit_new_ticket(self, data) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                f"{PROXY2_URL}/api/{DEPARTMENT}",
                headers={"Authorization": f"Bearer {self.token}"},
                json=data,
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_tickets()

    def action_edit_record(self) -> None:
        if self.active_tab() == "tab-pedidos":
            record = self.selected_pedido()
            if not record:
                self.notify("Selecciona un pedido primero", severity="warning")
                return

            def handle_status(new_status):
                if new_status:
                    self.run_worker(self.submit_edit_pedido(record["id"], new_status))

            self.push_screen(OrderStatusModal(record["id"], record["estado"]), handle_status)
            return

        record = self.selected_ticket()
        if not record:
            self.notify("Selecciona un ticket primero", severity="warning")
            return

        def handle_result(data):
            if data:
                self.run_worker(self.submit_edit_ticket(record["id"], data))

        self.push_screen(TicketModal(f"Editar — {TITLE}", initial=record), handle_result)

    async def submit_edit_ticket(self, record_id, data) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.put(
                f"{PROXY2_URL}/api/{DEPARTMENT}/{record_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                json=data,
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_tickets()

    async def submit_edit_pedido(self, order_id, new_status) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.put(
                f"{PROXY2_URL}/api/pedidos/{order_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"estado": new_status},
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_pedidos()

    def action_delete_record(self) -> None:
        if self.active_tab() == "tab-pedidos":
            self.notify("Los pedidos no se pueden eliminar", severity="warning")
            return

        record = self.selected_ticket()
        if not record:
            self.notify("Selecciona un ticket primero", severity="warning")
            return

        def handle_result(confirmed):
            if confirmed:
                self.run_worker(self.submit_delete_ticket(record["id"]))

        self.push_screen(ConfirmModal(f"¿Eliminar ticket #{record['id']}?"), handle_result)

    async def submit_delete_ticket(self, record_id) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.delete(
                f"{PROXY2_URL}/api/{DEPARTMENT}/{record_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_tickets()


if __name__ == "__main__":
    DepartmentApp().run()
