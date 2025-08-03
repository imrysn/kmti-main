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
        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
        expand=True,
    )

    page.overlay.append(overlay)
    page.update()


def show_confirm_dialog(page: ft.Page, title: str, message: str, on_confirm):
    """
    Same style as show_center_sheet but specifically for confirmation.
    """
    show_center_sheet(page, title, message, on_confirm)


def show_input_dialog(page: ft.Page, title: str, hint: str, on_submit):
    """
    Input dialog similar in style to show_center_sheet.
    """
    text_field = ft.TextField(label=hint, width=300)

    def close_overlay(e=None):
        if overlay in page.overlay:
            page.overlay.remove(overlay)
        page.update()

    def submit_action(e):
        val = text_field.value.strip()
        close_overlay()
        if on_submit:
            on_submit(val)

    overlay = ft.Container(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    text_field,
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
                                "Submit",
                                on_click=submit_action,
                                style=ft.ButtonStyle(
                                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                             ft.ControlState.HOVERED: ft.Colors.WHITE},
                                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.BLUE},
                                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                                          ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                                    shape=ft.RoundedRectangleBorder(radius=5),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                    )
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
        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
        expand=True,
    )

    page.overlay.append(overlay)
    page.update()
