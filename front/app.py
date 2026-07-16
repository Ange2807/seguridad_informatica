"""
SECURECORP — TUI Frontend
Punto de entrada principal de la aplicación Textual.
"""
from pathlib import Path
from textual.app import App

from api import ApiClient
from screens.login import LoginScreen
from screens.staff import StaffScreen


class SecureCorpApp(App):
    """Aplicación TUI para la plataforma SECURECORP."""

    TITLE = "SECURECORP"
    SUB_TITLE = "Plataforma de Seguridad Empresarial"
    CSS_PATH = Path("styles/theme.tcss")

    # Crea el cliente HTTP compartido por todas las pantallas.
    def __init__(self):
        super().__init__()
        self.api = ApiClient()

    # Muestra la pantalla de login al arrancar la app.
    def on_mount(self) -> None:
        self.push_screen(LoginScreen())

    # ── Navegación ───────────────────────────────────────

    # Cambia a la pantalla principal de staff tras el login.
    def show_staff(self) -> None:
        self.switch_screen(StaffScreen())

    # Vuelve a la pantalla de login.
    def show_login(self) -> None:
        self.switch_screen(LoginScreen())

    # Cierra la sesión actual y vuelve al login.
    def do_logout(self) -> None:
        self.api.logout()
        self.show_login()


if __name__ == "__main__":
    app = SecureCorpApp()
    app.run()
