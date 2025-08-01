import flet as ft
from flet import FontWeight
from typing import Optional
from pathlib import Path
import os

# Change this to your server folder
BASE_DIR = Path(r"X:\PROJECTS")


def list_directory(path: Path):
    folders = []
    files = []
    try:
        for item in sorted(path.iterdir()):
            if item.is_dir():
                folders.append(item)
            else:
                files.append(item)
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
    return folders, files


def search_all(base: Path, query: str):
    results = []
    try:
        for root, dirs, files in os.walk(base):
            for d in dirs:
                if query.lower() in d.lower():
                    results.append(Path(root) / d)
            for f in files:
                if query.lower() in f.lower():
                    results.append(Path(root) / f)
    except Exception as e:
        print(f"Error searching {base}: {e}")
    return results


def data_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    current_path = [BASE_DIR]

    # Grid for displaying folders/files
    grid = ft.GridView(
        expand=True,
        runs_count=6,
        max_extent=150,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
    )

    # Text field for search
    search_field = ft.TextField(
        hint_text="Search...",
        width=250,
        height=40,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
    )

    # Back button
    back_button = ft.IconButton(
        ft.Icons.ARROW_BACK,
        tooltip="Back",
        on_click=lambda e: go_back(),
        visible=False
    )

    def open_item(item: Path):
        if item.is_dir():
            current_path[0] = item
            refresh()
        else:
            os.startfile(item)  # Opens file with default application

    def go_back():
        if current_path[0] != BASE_DIR:
            current_path[0] = current_path[0].parent
            refresh()

    def build_item_tile(item: Path):
        is_folder = item.is_dir()
        icon = ft.Icons.FOLDER if is_folder else ft.Icons.DESCRIPTION
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=64, color="#000000"),
                ft.Text(item.name, size=14, text_align="center", no_wrap=False),
            ], alignment=ft.MainAxisAlignment.CENTER),
            on_click=lambda e, p=item: open_item(p),
            padding=10,
            border_radius=8,
        )

    def refresh():
        grid.controls.clear()
        path = current_path[0]

        # Toggle back button
        back_button.visible = (path != BASE_DIR)

        # If search is active, perform search
        query = search_field.value.strip()
        if query:
            results = search_all(BASE_DIR, query)
            for item in results:
                grid.controls.append(build_item_tile(item))
        else:
            folders, files = list_directory(path)
            for f in folders + files:
                grid.controls.append(build_item_tile(f))

        grid.update()
        back_button.update()

    # Attach refresh to search field change
    search_field.on_change = lambda e: refresh()

    # Layout top bar
    top_bar = ft.Row([
        back_button,
        ft.PopupMenuButton(
            icon=ft.Icons.UPLOAD,
            items=[
                ft.PopupMenuItem(text="Upload File"),
                ft.PopupMenuItem(text="Upload Folder")
            ]
        ),
        ft.PopupMenuButton(
            icon=ft.Icons.CREATE_NEW_FOLDER,
            items=[
                ft.PopupMenuItem(text="New Folder"),
                ft.PopupMenuItem(text="New File")
            ]
        ),
        ft.Container(expand=True),
        search_field,
    ], alignment=ft.MainAxisAlignment.START)

    # Add controls
    content.controls.extend([
        top_bar,
        ft.Divider(),
        grid
    ])
    content.update()

    # Initial refresh
    refresh()
