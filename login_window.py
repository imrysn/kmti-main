import flet as ft
from utils.auth import validate_login
from admin_panel import admin_panel
from user_panel import user_panel
from flet import FontWeight, CrossAxisAlignment, MainAxisAlignment
from typing import Optional

def login_view(page: ft.Page):
    # Set page properties
    page.title = "Login"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = "#D9D9D9"  # Light gray background
    
    # State variable for login type
    is_admin_login = False
    
    # Create controls
    username = ft.TextField(
        label="Username",
        width=300,
        border_radius=10,
        height=50,
        border_color="#cccccc",
        focused_border_color="#000000",
        bgcolor=ft.Colors.WHITE
    )
    
    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=10,
        height=50,
        border_color="#cccccc",
        focused_border_color="#000000",
        bgcolor=ft.Colors.WHITE
    )
    
    error_text = ft.Text("", color="red")
    login_type_text = ft.Text("USER", size=18, weight=FontWeight.W_500)
    
    def login_action(e):
        role = validate_login(username.value, password.value, is_admin_login)
        if role == "admin":
            page.clean()
            admin_panel(page, username.value)
        elif role == "user":
            page.clean()
            user_panel(page, username.value)
        else:
            error_text.value = "Invalid credentials!"
            page.update()

    # Reset password text
    reset_password = ft.Text(
        "Reset password",
        color="#000000",
        weight=FontWeight.W_500,
        size=12
    )
    
    # Toggle between admin and user login
    def toggle_login_type(e):
        nonlocal is_admin_login
        is_admin_login = not is_admin_login
        login_type_text.value = "ADMINISTRATOR" if is_admin_login else "USER"
        page.update()
    
    login_type_switch = ft.TextButton(
        content=ft.Text(
            "Login as Administrator" if not is_admin_login else "Login as User",
            color="#000000",
            size=12
        ),
        on_click=toggle_login_type
    )

    # Create the login card
    login_card = ft.Card(
        elevation=5,
        content=ft.Container(
            width=400,
            padding=40,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_400),
            border_radius=10,
            content=ft.Column(
                [
                    login_type_text,
                    ft.Divider(height=20, color="transparent"),
                    username,
                    password,
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton(
                        "Login",
                        on_click=login_action,
                        width=150,
                        height=45,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            bgcolor={
                                ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                ft.ControlState.HOVERED: ft.Colors.WHITE
                            },
                            side={
                                ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)
                            },
                            color={
                                ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                ft.ControlState.HOVERED: ft.Colors.BLACK
                            }
                        )
                    ),
                    reset_password,
                    error_text,
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=5
            )
        )
    )
    
    # Create a column for all elements
    main_column = ft.Column(
        [
            ft.Image(src="assets/kmti_logo.png", width=150),
            ft.Divider(height=30, color="transparent"),
            login_card,
            ft.Divider(height=20, color="transparent"),
            login_type_switch
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=0
    )
    
    # Add everything to the page
    page.add(main_column)