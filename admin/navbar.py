import flet as ft
from flet import FontWeight


def create_navbar(username: str, on_nav, on_logout):

    menu_items = [
        "Dashboard",
        "Data Management",
        "User Management",
        "Activity Logs",
        "System Settings",
    ]

    active_index = {"value": 0}
    buttons: list[ft.TextButton] = []

    # Apply styles based on which tab is active
    def refresh_buttons():
        for i, btn in enumerate(buttons):
            if i == active_index["value"]:
                btn.content.weight = FontWeight.NORMAL
                btn.content.style = ft.TextStyle(
                    decoration=ft.TextDecoration.UNDERLINE,
                    decoration_color=ft.Colors.WHITE,
                )
            else:
                btn.content.weight = FontWeight.NORMAL
                btn.content.style = ft.TextStyle(decoration=None)

    # Handle click on a menu item
    def handle_click(index: int):
        active_index["value"] = index
        refresh_buttons()
        for btn in buttons:
            btn.update()
        on_nav(index)

    # Create a button for each menu item
    for index, label in enumerate(menu_items):
        btn = ft.TextButton(
            content=ft.Text(label, size=16),
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                padding=10,
            ),
            on_click=lambda e, i=index: handle_click(i),
        )
        buttons.append(btn)

    # Center section: menu items evenly spaced
    center_row = ft.Row(
        controls=buttons,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=30,
        expand=True,
    )

    # Right section: user info + logout
    right_section = ft.Row(
        controls=[
            ft.Text(f"Hi, {username}", size=14,
                    color=ft.Colors.WHITE),
            ft.TextButton(
                content=ft.Text("Logout", size=14, color=ft.Colors.WHITE),
                on_click=lambda e: on_logout(),
            ),
        ],
        alignment=ft.MainAxisAlignment.END,
        spacing=20,
    )

    # Combine into a horizontal navbar
    navbar = ft.Container(
        bgcolor=ft.Colors.GREY_700,
        padding=10,
        content=ft.Row(
            controls=[
                center_row,
                right_section,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # Set initial active button style
    refresh_buttons()

    return navbar
