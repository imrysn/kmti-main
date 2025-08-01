import flet as ft

def show_center_sheet(page: ft.Page, title: str, message: str, on_confirm):
    """
    Creates a custom centered confirmation dialog that appears as an overlay.
    """

    def close_overlay(e=None):
        if overlay in page.overlay:
            page.overlay.remove(overlay)
        page.update()

    def confirm_action(e):
        close_overlay()
        if on_confirm:
            on_confirm()

    overlay = ft.Container(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(message, size=16),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Cancel", 
                                on_click=close_overlay,
                                style=ft.ButtonStyle(
                                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                            ft.ControlState.HOVERED: ft.Colors.BLACK},
                                    color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                        ft.ControlState.HOVERED: ft.Colors.WHITE},
                                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                                    shape=ft.RoundedRectangleBorder(radius=5),
                                ),
                        ),
                            ft.ElevatedButton(
                                "Confirm",
                                on_click=confirm_action,
                                style=ft.ButtonStyle(
                                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.RED,
                                            ft.ControlState.HOVERED: ft.Colors.WHITE},
                                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                        ft.ControlState.HOVERED: ft.Colors.RED},
                                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                                    shape=ft.RoundedRectangleBorder(radius=5),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            width=350,
            height=200,
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),  # Dimmed background
        expand=True,
    )

    page.overlay.append(overlay)
    page.update()
