import flet as ft
from admin.components.file_approval_panel import FileApprovalPanel
from utils.session_logger import log_logout


def TLPanel(page: ft.Page, username: str):
    page.title = "KMTI Data Management System Team Leader"
    page.bgcolor = ft.Colors.WHITE
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0  # remove page padding/margin

    # Main content container
    content = ft.Column(expand=True, spacing=0)

    # Navbar (full width at top, no margin)
    navbar = ft.Container(
        bgcolor=ft.Colors.GREY_800,
        padding=10,
        margin=0,  # ensure no extra margin
        content=ft.Row(
            [
                ft.Container(expand=True),
                ft.TextButton(
                    content=ft.Text("Logout", size=16, color=ft.Colors.WHITE),
                    on_click=lambda e: on_logout(),
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        ),
    )

    # Add navbar + content to page first
    page.add(navbar, content)

    # --- Logout function ---
    def on_logout():
        from login_window import clear_session  # avoid circular import
        log_logout(username, "TEAM LEADER")
        clear_session(username)
        page.clean()
        from login_window import login_view
        login_view(page)

    # --- Show File Approval Panel ---
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

    show_file_approval()
