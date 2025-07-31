import flet as ft
from login_window import login_view

def main(page: ft.Page):
    # Set window properties first
    page.title = "KMTI Data Management System"
    page.window_icon = "assets/kmti.ico" 
    page.theme_mode = ft.ThemeMode.LIGHT

    login_view(page)

    page.update()

ft.app(
    target=main,
    assets_dir="assets",
    view=ft.AppView.FLET_APP
)