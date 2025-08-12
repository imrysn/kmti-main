
import flet as ft

def confirm_action(page, title, message, on_confirm):
    def yes_click(e):
        page.dialog.open = False
        page.update()
        on_confirm()

    def no_click(e):
        page.dialog.open = False
        page.update()

    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Yes", on_click=yes_click),
            ft.TextButton("No", on_click=no_click)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog.open = True
    page.update()


def prompt_folder_name(page, title, message, on_submit):
    name_field = ft.TextField(label="Folder Name", autofocus=True)

    def submit_click(e):
        if name_field.value.strip() == "":
            name_field.error_text = "Folder name cannot be empty"
            page.dialog.update()
            return
        page.dialog.open = False
        page.update()
        on_submit(name_field.value.strip())

    def cancel_click(e):
        page.dialog.open = False
        page.update()

    page.dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Column([ft.Text(message), name_field], tight=True),
        actions=[
            ft.TextButton("Create", on_click=submit_click),
            ft.TextButton("Cancel", on_click=cancel_click)
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog.open = True
    page.update()
