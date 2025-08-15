import flet as ft
from admin.file_approval_panel import FileApprovalPanel
from utils.session_logger import log_logout


def TLPanel(page: ft.Page, username: str):
    page.title = "KMTI Data Management System Team Leader"
    page.bgcolor = ft.Colors.GREY_100
    page.padding = 0

    content = ft.Column(expand=True, spacing=0)

    def on_logout():
        from login_window import clear_session
        log_logout(username, "TEAM LEADER")
        clear_session(username)
        page.clean()
        from login_window import login_view
        login_view(page)

    navbar = ft.Container(
        bgcolor=ft.Colors.GREY_800,
        padding=10,
        margin=0,
        content=ft.Row(
            controls=[
                ft.Container(expand=True),  
                ft.Row(
                    controls=[
                        ft.Text(f"Hi, {username}", size=16, color=ft.Colors.WHITE),
                        ft.TextButton(
                            content=ft.Text("Logout", size=16, color=ft.Colors.WHITE),
                            on_click=lambda e: on_logout(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # Show File Approval Panel
    def show_file_approval():
        content.controls.clear()
        try:
            approval_panel = FileApprovalPanel(page, username)
            content.controls.append(approval_panel.create_approval_interface())
        except Exception as ex:
            print(f"[ERROR] Failed to load File Approval Panel: {ex}")
            content.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"Error loading panel: {ex}", color=ft.Colors.RED
                    )
                )
            )
        content.update()

    page.add(navbar, content)
    show_file_approval()
