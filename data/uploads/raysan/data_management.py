
import os
import shutil
import datetime
import flet as ft
from flet import icons
from utils.dialog import show_input_dialog, confirm_action
from utils.preview import preview_file
from utils.utils import readable_size, get_icon_and_color

ROOT_PATH = "./data"
LOG_FILE = "./logs/activity.log"

global_index = {}

def index_files():
    global global_index
    global_index = {}
    for root, dirs, files in os.walk(ROOT_PATH):
        for file in files:
            full_path = os.path.join(root, file)
            global_index[file.lower()] = full_path

def log_action(action, username="admin"):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.datetime.now()} - {username} - {action}\n")

def create_new_folder_dialog(page, path, refresh_ui):
    def on_submit(name):
        if not name:
            return
        new_folder_path = os.path.join(path, name)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
            log_action(f"Created folder: {new_folder_path}")
        refresh_ui()

    show_input_dialog(page, "New Folder", "Enter folder name", on_submit)

def delete_item(path, refresh_ui):
    def on_confirm():
        try:
            if os.path.isfile(path):
                os.remove(path)
                log_action(f"Deleted file: {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                log_action(f"Deleted folder: {path}")
            refresh_ui()
        except Exception as e:
            print("Delete error:", e)
    confirm_action("Are you sure you want to delete this item?", on_confirm)

def data_management(page, username):
    index_files()

    selected_path = ft.Ref[ft.Text]()
    file_picker = ft.FilePicker()

    selected_container = ft.Ref[ft.Container]()
    details_column = ft.Ref[ft.Column]()
    file_list_column = ft.Ref[ft.Column]()

    current_path = [ROOT_PATH]

    def refresh_file_list():
        file_list_column.current.controls.clear()
        details_column.current.controls.clear()
        try:
            entries = os.listdir(current_path[0])
            entries.sort()
            for entry in entries:
                full_path = os.path.join(current_path[0], entry)
                icon, color = get_icon_and_color(full_path)
                is_file = os.path.isfile(full_path)

                def on_click_entry(e, path=full_path):
                    for ctrl in file_list_column.current.controls:
                        ctrl.bgcolor = None
                    e.control.bgcolor = ft.colors.BLUE_100
                    selected_path.current.value = path
                    update_details(path)
                    page.update()

                def on_double_click(e, path=full_path):
                    if os.path.isdir(path):
                        current_path[0] = path
                        refresh_file_list()

                row = ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color),
                        ft.Text(entry, overflow="ellipsis", expand=True),
                    ]),
                    on_click=on_click_entry,
                    on_double_click=on_double_click,
                    data=full_path,
                    padding=5,
                    border_radius=5,
                    ink=True
                )

                def handle_rmb(e):
                    if e.name == "secondary":
                        context = ft.PopupMenuButton(items=[
                            ft.PopupMenuItem(text="Open", on_click=lambda _: on_double_click(e)),
                            ft.PopupMenuItem(text="Delete", on_click=lambda _: delete_item(full_path, refresh_file_list)),
                        ])
                        page.overlay.append(context)
                        page.update()

                row.on_long_press = handle_rmb
                file_list_column.current.controls.append(row)

        except Exception as e:
            file_list_column.current.controls.append(ft.Text(f"Error: {str(e)}"))

        page.update()

    def update_details(path):
        details_column.current.controls.clear()
        if not path:
            return
        name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        stat = os.stat(path)

        info = [
            f"Name: {name}",
            f"Type: {'Folder' if is_dir else 'File'}",
            f"Size: {'-' if is_dir else readable_size(stat.st_size)}",
            f"Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}",
            f"Path: {path}",
        ]
        for i in info:
            details_column.current.controls.append(ft.Text(i, size=12))
        if not is_dir:
            details_column.current.controls.append(
                ft.ElevatedButton("Preview", on_click=lambda e: preview_file(page, path))
            )
        details_column.current.controls.append(
            ft.ElevatedButton("Delete", on_click=lambda e: delete_item(path, refresh_file_list))
        )
        page.update()

    def upload_files():
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    dest = os.path.join(current_path[0], f.name)
                    shutil.copy(f.path, dest)
                    log_action(f"Uploaded file: {f.name}")
                refresh_file_list()

        file_picker.on_result = on_result
        page.overlay.append(file_picker)
        file_picker.pick_files(allow_multiple=True)

    breadcrumb = ft.Text(current_path[0], size=12)

    toolbar = ft.Row([
        ft.ElevatedButton("New Folder", on_click=lambda e: create_new_folder_dialog(page, current_path[0], refresh_file_list)),
        ft.ElevatedButton("Upload", on_click=lambda e: upload_files()),
        breadcrumb,
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    file_list_column.current = ft.Column(scroll=ft.ScrollMode.AUTO)
    details_column.current = ft.Column(scroll=ft.ScrollMode.AUTO)

    file_browser = ft.Container(
        content=ft.Row([
            ft.Container(
                content=file_list_column.current,
                width=600,
                height=500,
                padding=10,
                bgcolor=ft.colors.GREY_100,
                border_radius=5,
                expand=True
            ),
            ft.VerticalDivider(),
            ft.Container(
                content=details_column.current,
                width=300,
                height=500,
                padding=10,
                bgcolor=ft.colors.BLUE_50,
                border_radius=5,
                alignment=ft.alignment.top_center
            )
        ])
    )

    content = ft.Column([
        toolbar,
        file_browser
    ])

    page.clean()
    page.add(content)
    refresh_file_list()
