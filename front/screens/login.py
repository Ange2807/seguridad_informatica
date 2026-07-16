"""
Pantalla de Login — Exclusiva para Empleados (Staff).
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button, Header, Footer
from textual.containers import Vertical, Horizontal, Center


class LoginScreen(Screen):
    """Pantalla de autenticación para Staff."""

    BINDINGS = [("ctrl+q", "quit", "Salir")]

    # Dibuja el formulario de login/registro de staff.
    def compose(self) -> ComposeResult:
        yield Header()
        with Center(id="login-wrapper"):
            with Vertical(id="login-box"):
                yield Static(
                    "╔═══════════════════════════════════════╗\n"
                    "║       🔒  S E C U R E C O R P        ║\n"
                    "╚═══════════════════════════════════════╝",
                    id="logo-text",
                )
                yield Static("Plataforma de Seguridad Empresarial (Staff)", id="subtitle-text")

                yield Input(placeholder="Cédula (ej: 00000001)", id="staff-cedula")
                yield Input(placeholder="Usuario", id="staff-user")
                yield Input(placeholder="Contraseña", password=True, id="staff-pass")
                with Horizontal(classes="login-buttons"):
                    yield Button("Ingresar", variant="primary", id="btn-staff-login")
                    yield Button("Registrarse", variant="default", id="btn-staff-register")

                yield Static("", id="login-error")
        yield Footer()

    # ── Eventos ──────────────────────────────────────────

    # Maneja login y auto-registro de staff según el botón presionado.
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        error_w = self.query_one("#login-error", Static)
        error_w.update("")

        try:
            # [SEGURIDAD] Se valida el input de forma reactiva ( frontend ) 
            # para mejorar la experiencia del usuario y evitar peticiones innecesarias al servidor.
            # Sin embargo, la validación final (authorization) la realiza el backend (Proxy2).
            if btn == "btn-staff-login":
                u = self.query_one("#staff-user", Input).value.strip()
                p = self.query_one("#staff-pass", Input).value
                if not u or not p:
                    error_w.update("⚠  Usuario y contraseña requeridos")
                    return
                await self.app.api.staff_login(u, p)
                self.app.show_staff()
                
            elif btn == "btn-staff-register":
                c = self.query_one("#staff-cedula", Input).value.strip()
                u = self.query_one("#staff-user", Input).value.strip()
                p = self.query_one("#staff-pass", Input).value
                if not c or not u or not p:
                    error_w.update("⚠  Cédula, usuario y contraseña requeridos")
                    return
                await self.app.api.staff_register(c, u, p)
                await self.app.api.staff_login(u, p)
                self.app.show_staff()

        except Exception as e:
            error_w.update(f"⚠  {e}")
