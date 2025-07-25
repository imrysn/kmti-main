import flet as ft
from login_window import login_view

def main(page: ft.Page):
    page.title = "KMTI Data Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.update()

    login_view(page)

ft.app(
    target=main,
    view=ft.AppView.FLET_APP 
)
