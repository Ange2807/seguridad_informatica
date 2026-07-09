"""
Pantalla de Login — Invitado / Empleado.
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button, Header, Footer, TabbedContent, TabPane
from textual.containers import Vertical, Horizontal, Center


class LoginScreen(Screen):
    """Pantalla de autenticación con pestañas Guest / Staff."""

    BINDINGS = [("ctrl+q", "quit", "Salir")]

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
                yield Static("Plataforma de Seguridad Empresarial", id="subtitle-text")

                with TabbedContent():
                    with TabPane("👤 Invitado", id="tab-guest"):
                        yield Input(placeholder="Usuario", id="guest-user")
                        yield Input(placeholder="Contraseña", password=True, id="guest-pass")
                        with Horizontal(classes="login-buttons"):
                            yield Button("Ingresar", variant="primary", id="btn-guest-login")
                            yield Button("Registrarse", variant="default", id="btn-guest-register")

                    with TabPane("🏢 Empleado", id="tab-staff"):
                        yield Input(placeholder="Cédula (ej: V-00000001)", id="staff-cedula")
                        yield Input(placeholder="Usuario", id="staff-user")
                        yield Input(placeholder="Contraseña", password=True, id="staff-pass")
                        with Horizontal(classes="login-buttons"):
                            yield Button("Ingresar", variant="primary", id="btn-staff-login")
                            yield Button("Registrarse", variant="default", id="btn-staff-register")

                yield Static("", id="login-error")
        yield Footer()

    # ── Eventos ──────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        error_w = self.query_one("#login-error", Static)
        error_w.update("")

        try:
            if btn == "btn-guest-login":
                u = self.query_one("#guest-user", Input).value.strip()
                p = self.query_one("#guest-pass", Input).value
                if not u or not p:
                    error_w.update("⚠  Usuario y contraseña requeridos")
                    return
                await self.app.api.guest_login(u, p)
                self.app.show_catalog()

            elif btn == "btn-guest-register":
                u = self.query_one("#guest-user", Input).value.strip()
                p = self.query_one("#guest-pass", Input).value
                if not u or not p:
                    error_w.update("⚠  Usuario y contraseña requeridos")
                    return
                await self.app.api.guest_register(u, p)
                await self.app.api.guest_login(u, p)
                self.app.show_catalog()

            elif btn == "btn-staff-login":
                u = self.query_one("#staff-user", Input).value.strip()
                p = self.query_one("#staff-pass", Input).value
                if not u or not p:
                    error_w.update("⚠  Usuario y contraseña requeridos")
                    return
                await self.app.api.staff_login(u, p)
                self.app.show_catalog()

            elif btn == "btn-staff-register":
                c = self.query_one("#staff-cedula", Input).value.strip()
                u = self.query_one("#staff-user", Input).value.strip()
                p = self.query_one("#staff-pass", Input).value
                if not c or not u or not p:
                    error_w.update("⚠  Cédula, usuario y contraseña requeridos")
                    return
                await self.app.api.staff_register(c, u, p)
                await self.app.api.staff_login(u, p)
                self.app.show_catalog()

        except Exception as e:
            error_w.update(f"⚠  {e}")
