import os

import httpx
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

PROXY2_URL = os.environ.get("PROXY2_URL", "http://proxy2:4000")
DEPARTMENT = os.environ.get("DEPARTMENT", "rrhh")
TITLE = "Recursos Humanos"
FIELDS = [
    ("cedula", "Cédula"),
    ("nombre", "Nombre"),
    ("cargo", "Cargo (atencion/rrhh/inventario/administrador)"),
]


class FormModal(ModalScreen):
    CSS = """
    FormModal { align: center middle; }
    #form-box { width: 58; border: round $accent; padding: 1 2; background: $surface; }
    #form-box Input { margin-bottom: 1; }
    """

    # Guarda el título del formulario y los valores iniciales si existen.
    def __init__(self, form_title, initial=None):
        super().__init__()
        self.form_title = form_title
        self.initial = initial or {}

    # Construye el modal para crear o editar empleados.
    def compose(self) -> ComposeResult:
        with Vertical(id="form-box"):
            yield Label(self.form_title)
            for key, label in FIELDS:
                yield Input(value=str(self.initial.get(key, "")), placeholder=label, id=f"field-{key}")
            with Horizontal():
                yield Button("Guardar", id="save", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

    @on(Button.Pressed, "#save")
    # Devuelve los datos del formulario al cerrar con Guardar.
    def save(self) -> None:
        data = {key: self.query_one(f"#field-{key}", Input).value for key, _ in FIELDS}
        self.dismiss(data)

    # Cierra el modal sin aplicar cambios.
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

    # Construye el modal de auto-registro por cédula.
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

    # Envía la cédula y credenciales al backend para crear la cuenta interna.
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

    # Cierra el modal de registro sin crear usuario.
    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class DepartmentApp(App):
    CSS = """
    Screen { align: center middle; }
    #login-box { width: 58; border: round $accent; padding: 1 2; }
    #status { height: 1; color: $error; }
    #main { width: 1fr; height: 1fr; padding: 1 2; }
    #search { width: 1fr; margin-bottom: 1; }
    DataTable { height: 1fr; width: 1fr; }
    """

    BINDINGS = [
        ("n", "new_record", "Nuevo"),
        ("e", "edit_record", "Editar"),
        ("r", "refresh", "Refrescar"),
    ]

    # Inicializa el estado de la app de RRHH.
    def __init__(self):
        super().__init__()
        self.token = None
        self.current_records = []

    # Dibuja la pantalla de login inicial.
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

    # Ajusta el título y enfoca el campo usuario al iniciar.
    def on_mount(self) -> None:
        self.title = TITLE
        self.query_one("#username", Input).focus()

    # Pasa el foco a la contraseña cuando se completa el usuario.
    @on(Input.Submitted, "#username")
    def focus_password(self) -> None:
        self.query_one("#password", Input).focus()

    # Ejecuta el intento de inicio de sesión.
    @on(Button.Pressed, "#login-btn")
    async def login_button_pressed(self) -> None:
        await self.handle_login()

    # Abre el modal de auto-registro y rellena el usuario si fue exitoso.
    @on(Button.Pressed, "#register-btn")
    def open_register(self) -> None:
        # Copia el usuario recién creado al formulario de login.
        def handle_result(result):
            if result:
                self.query_one("#username", Input).value = result["username"]
                self.query_one("#status", Static).update(
                    f"Cuenta creada (cargo: {result.get('cargo')}). Ya puedes iniciar sesión."
                )

        self.push_screen(RegisterModal(), handle_result)

    # Intenta autenticación LDAP y, si falla, login por cuenta auto-registrada.
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

    # Reemplaza el login por la vista principal con tabla y buscador.
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

    # Recarga la tabla cuando el usuario confirma una búsqueda.
    @on(Input.Submitted, "#search")
    async def on_search(self) -> None:
        await self.load_data()

    # Limpia el buscador y vuelve a pedir todos los registros.
    async def action_refresh(self) -> None:
        if not self.token:
            return
        self.query_one("#search", Input).value = ""
        await self.load_data()

    # Consulta la API y pinta los empleados en la tabla.
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

    # Devuelve el empleado actualmente seleccionado en la tabla.
    def selected_record(self):
        table = self.query_one("#table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None
        if table.cursor_row >= len(self.current_records):
            return None
        return self.current_records[table.cursor_row]

    # Abre el formulario para crear un nuevo empleado.
    def action_new_record(self) -> None:
        if not self.token:
            return

        # Envia el nuevo empleado cuando el modal devuelve datos.
        def handle_result(data):
            if data:
                self.run_worker(self.submit_new(data))

        self.push_screen(FormModal(f"Nuevo — {TITLE}"), handle_result)

    # Inserta un empleado nuevo en la base de datos.
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

    # Abre el formulario de edición para el empleado seleccionado.
    def action_edit_record(self) -> None:
        record = self.selected_record()
        if not record:
            self.notify("Selecciona un registro primero", severity="warning")
            return

        # Envía la edición al backend cuando el modal devuelve datos.
        def handle_result(data):
            if data:
                self.run_worker(self.submit_edit(record["id"], data))

        self.push_screen(FormModal(f"Editar — {TITLE}", initial=record), handle_result)

    # Actualiza un empleado existente.
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


if __name__ == "__main__":
    DepartmentApp().run()
