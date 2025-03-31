import flet as ft
from flet import icons
import logging
from views.shared import show_login
from database import DatabaseManager

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SportProApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._configure_page()
        self.db = DatabaseManager()
        show_login(page, self.db)

    def _configure_page(self):
        """Configura la página principal"""
        self.page.title = "SportPro - Gestión Deportiva"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#FFFFFF"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
            "RobotoSlab": "https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;700&display=swap"
        }
        self.page.theme = ft.Theme(
            font_family="Roboto",
            color_scheme=ft.ColorScheme(
                primary="#FF7F2A",
                secondary="#F5F5F5",
                surface="#FFFFFF",
                on_primary="#FFFFFF",
                on_secondary="#333333"
            ),
            text_theme=ft.TextTheme(
                title_large=ft.TextStyle(size=24, weight="bold"),
                title_medium=ft.TextStyle(size=20, weight="bold"),
                body_large=ft.TextStyle(size=16),
            )
        )

def main(page: ft.Page):
    app = SportProApp(page)
    db = DatabaseManager()

    def route_change(route):
        if page.route == "/register":
            from views.shared import show_register
            show_register(page, db)
        elif page.route == "/login":
            from views.shared import show_login
            show_login(page, db)

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        assets_dir="assets"
    )