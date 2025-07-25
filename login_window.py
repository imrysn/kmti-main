import flet as ft
from utils.auth import validate_login
from admin_panel import admin_panel
from user_panel import user_panel
from flet import FontWeight, CrossAxisAlignment
from typing import Optional

def login_view(page: ft.Page):
    username = ft.TextField(label="Username", width=300)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text("", color="red")

    def login_action(e):
        role = validate_login(username.value, password.value)
        if role == "admin":
            page.clean()
            admin_panel(page, username.value)
        elif role == "user":
            page.clean()
            user_panel(page, username.value)
        else:
            error_text.value = "Invalid credentials!"
            page.update()

    card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Image(src="assets/kmti_logo.png", width=120),
                ft.Text("USER LOGIN", weight=FontWeight.BOLD),
                username,
                password,
                ft.ElevatedButton("Login", on_click=login_action),
                error_text,
            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
            padding=20,
            alignment=ft.alignment.center
        )
    )
    page.add(ft.Container(content=card, alignment=ft.alignment.center, expand=True))
