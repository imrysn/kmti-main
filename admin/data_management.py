import flet as ft
from flet import FontWeight
from typing import Optional
from pathlib import Path
import os
import time
from utils.config_loader import get_base_dir

BASE_DIR = get_base_dir()


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
    selected_item = {"path": None}
    last_click_time = {"time": 0}

    grid = ft.GridView(
        expand=True,
        runs_count=6,
        max_extent=150,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
    )

    search_field = ft.TextField(
        hint_text="Search...",
        width=250,
        height=40,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
    )

    back_button = ft.IconButton(
        ft.Icons.ARROW_BACK,
        tooltip="Back",
        on_click=lambda e: go_back(),
        visible=False
    )

    # ---------------- Core functions ----------------

    def open_item(item: Path):
        if item.is_dir():
            current_path[0] = item
            refresh()
        else:
            os.startfile(item)

    def go_back():
        if current_path[0] != BASE_DIR:
            current_path[0] = current_path[0].parent
            refresh()

    def handle_click(item: Path):
        """Single click selects, double click opens."""
        now = time.time()
        # First click or different item -> select
        if selected_item["path"] != item or (now - last_click_time["time"]) > 0.5:
            selected_item["path"] = item
            last_click_time["time"] = now
            refresh()
        else:
            # Double click -> open
            open_item(item)
            selected_item["path"] = None
            refresh()

    def build_item_tile(item: Path):
        is_folder = item.is_dir()
        icon = ft.Icons.FOLDER if is_folder else ft.Icons.DESCRIPTION

        # Limit display name length
        display_name = item.name
        max_len = 15
        short_name = display_name if len(display_name) <= max_len else display_name[:max_len - 3] + "..."

        # Highlight selected
        bg_color = ft.Colors.with_opacity(0.5, ft.Colors.GREY_800) if selected_item["path"] == item else "transparent"

        container = ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=64, color="#000000"),
                ft.Text(short_name, size=14, text_align="center", no_wrap=True),
            ], alignment=ft.MainAxisAlignment.CENTER),
            tooltip=item.name,
            on_click=lambda e, p=item: handle_click(p),
            padding=10,
            border_radius=8,
            bgcolor=bg_color,
        )

        # Hover effect
        def on_hover(e):
            container.bgcolor =ft.Colors.with_opacity(0.2, ft.Colors.GREY_800) if e.data == "true" and selected_item["path"] != item else bg_color
            container.update()

        container.on_hover = on_hover
        return container

    def refresh():
        grid.controls.clear()
        path = current_path[0]
        back_button.visible = (path != BASE_DIR)

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

    search_field.on_change = lambda e: refresh()

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

    content.controls.extend([
        top_bar,
        ft.Divider(),
        grid
    ])
    content.update()

    refresh()
