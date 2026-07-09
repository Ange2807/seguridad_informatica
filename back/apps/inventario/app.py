import os

import httpx
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

PROXY2_URL = os.environ.get("PROXY2_URL", "http://proxy2:4000")
DEPARTMENT = os.environ.get("DEPARTMENT", "inventario")
TITLE = "Inventario"
FIELDS = [
    ("producto", "Producto"),
    ("cantidad", "Cantidad"),
    ("ubicacion", "Ubicación"),
    ("precio", "Precio"),
]


class FormModal(ModalScreen):
    CSS = """
    FormModal { align: center middle; }
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
            for key, label in FIELDS:
                yield Input(value=str(self.initial.get(key, "")), placeholder=label, id=f"field-{key}")
            with Horizontal():
                yield Button("Guardar", id="save", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        data = {key: self.query_one(f"#field-{key}", Input).value for key, _ in FIELDS}
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
    #search { width: 1fr; margin-bottom: 1; }
    DataTable { height: 1fr; width: 1fr; }
    """

    BINDINGS = [
        ("n", "new_record", "Nuevo"),
        ("e", "edit_record", "Editar"),
        ("d", "delete_record", "Eliminar"),
        ("r", "refresh", "Refrescar"),
    ]

    def __init__(self):
        super().__init__()
        self.token = None
        self.current_records = []

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

    def on_mount(self) -> None:
        self.title = TITLE
        self.query_one("#username", Input).focus()

    @on(Input.Submitted, "#username")
    def focus_password(self) -> None:
        self.query_one("#password", Input).focus()

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
        await main.mount(Input(placeholder="Buscar... (Enter para buscar)", id="search"))
        table = DataTable(id="table")
        table.cursor_type = "row"
        await main.mount(table)
        await self.load_data()
        self.query_one("#search", Input).focus()

    @on(Input.Submitted, "#search")
    async def on_search(self) -> None:
        await self.load_data()

    async def action_refresh(self) -> None:
        if not self.token:
            return
        self.query_one("#search", Input).value = ""
        await self.load_data()

    async def load_data(self) -> None:
        if not self.token:
            return
        query = self.query_one("#search", Input).value
        params = {"q": query} if query else {}
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{PROXY2_URL}/api/{DEPARTMENT}",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
            )
            rows = res.json()
        table = self.query_one("#table", DataTable)
        table.clear(columns=True)
        self.current_records = rows if isinstance(rows, list) else []
        columns = [key for key, _ in FIELDS]
        table.add_columns("id", *columns)
        if self.current_records:
            for row in self.current_records:
                table.add_row(str(row["id"]), *[str(row.get(c, "")) for c in columns])
        else:
            table.add_row("-", *["sin registros" for _ in columns])

    def selected_record(self):
        table = self.query_one("#table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self.current_records):
            return None
        return self.current_records[table.cursor_row]

    def action_new_record(self) -> None:
        if not self.token:
            return

        def handle_result(data):
            if data:
                self.run_worker(self.submit_new(data))

        self.push_screen(FormModal(f"Nuevo — {TITLE}"), handle_result)

    async def submit_new(self, data) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                f"{PROXY2_URL}/api/{DEPARTMENT}",
                headers={"Authorization": f"Bearer {self.token}"},
                json=data,
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_data()

    def action_edit_record(self) -> None:
        record = self.selected_record()
        if not record:
            self.notify("Selecciona un registro primero", severity="warning")
            return

        def handle_result(data):
            if data:
                self.run_worker(self.submit_edit(record["id"], data))

        self.push_screen(FormModal(f"Editar — {TITLE}", initial=record), handle_result)

    async def submit_edit(self, record_id, data) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.put(
                f"{PROXY2_URL}/api/{DEPARTMENT}/{record_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                json=data,
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_data()

    def action_delete_record(self) -> None:
        record = self.selected_record()
        if not record:
            self.notify("Selecciona un registro primero", severity="warning")
            return

        def handle_result(confirmed):
            if confirmed:
                self.run_worker(self.submit_delete(record["id"]))

        self.push_screen(ConfirmModal(f"¿Eliminar registro #{record['id']}?"), handle_result)

    async def submit_delete(self, record_id) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.delete(
                f"{PROXY2_URL}/api/{DEPARTMENT}/{record_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if res.status_code >= 400:
                self.notify(f"Error: {res.json().get('error')}", severity="error")
        await self.load_data()


if __name__ == "__main__":
    DepartmentApp().run()
