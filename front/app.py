"""
SECURECORP — TUI Frontend
Punto de entrada principal de la aplicación Textual.
"""
from pathlib import Path
from textual.app import App

from api import ApiClient
from screens.login import LoginScreen
from screens.catalog import CatalogScreen
from screens.orders import OrdersScreen
from screens.staff import StaffScreen


class SecureCorpApp(App):
    """Aplicación TUI para la plataforma SECURECORP."""

    TITLE = "SECURECORP"
    SUB_TITLE = "Plataforma de Seguridad Empresarial"
    CSS_PATH = Path("styles/theme.tcss")

    def __init__(self):
        super().__init__()
        self.api = ApiClient()
        self.cart: list[dict] = []

    def on_mount(self) -> None:
        self.push_screen(LoginScreen())

    # ── Navegación ───────────────────────────────────────

    def show_catalog(self) -> None:
        self.switch_screen(CatalogScreen())

    def show_orders(self) -> None:
        self.switch_screen(OrdersScreen())

    def show_staff(self) -> None:
        self.switch_screen(StaffScreen())

    def show_login(self) -> None:
        self.switch_screen(LoginScreen())

    def do_logout(self) -> None:
        self.api.logout()
        self.cart.clear()
        self.show_login()


if __name__ == "__main__":
    app = SecureCorpApp()
    app.run()
