import flet as ft
from flet import FontWeight
from typing import Optional
from pathlib import Path
import os
import time
import threading
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog
from admin.details_pane import DetailsPane

BASE_DIR = get_base_dir()

# Cache for search results
search_cache = {}


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


def search_all(base: Path, query: str, max_results=500):
    """
    Optimized search with limit to avoid GUI freezing.
    """
    results = []
    lower_query = query.lower()
    try:
        for root, dirs, files in os.walk(base):
            for d in dirs:
                if lower_query in d.lower():
                    results.append(Path(root) / d)
                    if len(results) >= max_results:
                        return results
            for f in files:
                if lower_query in f.lower():
                    results.append(Path(root) / f)
                    if len(results) >= max_results:
                        return results
    except Exception as e:
        print(f"Error searching {base}: {e}")
    return results


def data_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    current_path = [BASE_DIR]
    selected_item = {"path": None}
    last_click_time = {"time": 0}
    search_thread = {"thread": None}

    # Grid for files/folders
    grid = ft.GridView(
        expand=True,
        runs_count=6,
        max_extent=150,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
    )

    # Details pane
    details_panel = DetailsPane()

    search_field = ft.TextField(
        hint_text="Search...",
        width=300,
        height=40,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
    )

    # Breadcrumb container
    breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)

    back_button = ft.IconButton(
        ft.Icons.ARROW_BACK,
        tooltip="Back",
        on_click=lambda e: go_back(),
        visible=False,
    )

    # ---------------- Core functions ----------------

    def update_breadcrumb():
        breadcrumb.controls.clear()
        parts = list(current_path[0].parts)
        for i, part in enumerate(parts):
            partial_path = Path(*parts[: i + 1])

            def go_to_path(_, p=partial_path):
                current_path[0] = p
                refresh()

            # Create clickable button for each path segment
            breadcrumb.controls.append(
                ft.TextButton(
                    text=part,
                    on_click=go_to_path,
                    style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: ft.Colors.BLUE}),
                )
            )
            if i < len(parts) - 1:
                breadcrumb.controls.append(ft.Text(">", weight=FontWeight.BOLD))

        breadcrumb.update()

    def show_details(item: Path):
        """Show details of selected file/folder in the right pane."""
        details_panel.update_details(item)

    def highlight_selected():
        """Highlight the selected item with a grey border."""
        for tile in grid.controls:
            path = tile.data
            if path == selected_item["path"]:
                tile.border = ft.border.all(2, ft.Colors.GREY_800)
            else:
                tile.border = None
            tile.update()

    def open_item(item: Path):
        if item.is_dir():
            current_path[0] = item
            refresh()
        else:
            # Confirm before opening file
            def confirm_open():
                os.startfile(item)

            show_confirm_dialog(
                content.page,
                "Open File",
                f"Are you sure you want to open '{item.name}'?",
                confirm_open,
            )

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
            highlight_selected()
            show_details(item)
        else:
            # Double click -> open
            open_item(item)
            selected_item["path"] = None
            refresh()

    def get_icon_and_color(item: Path):
        """Return icon and color based on file type."""
        if item.is_dir():
            return ft.Icons.FOLDER, "#000000"

        ext = item.suffix.lower()
        if ext == ".pdf":
            return ft.Icons.PICTURE_AS_PDF, "red"
        elif ext in [".xlsx", ".xls"]:
            return ft.Icons.TABLE_CHART, "green"
        elif ext in [".zip", ".rar"]:
            return ft.Icons.FOLDER_ZIP, "orange"
        elif ext in [".icd", ".dwg"]:
            return ft.Icons.ARCHITECTURE, "#f0a500"
        else:
            return ft.Icons.DESCRIPTION, "#000000"

    def build_item_tile(item: Path):
        icon, color = get_icon_and_color(item)

        # Limit display name length
        display_name = item.name
        max_len = 15
        short_name = display_name if len(display_name) <= max_len else display_name[:max_len - 3] + "..."

        container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=64, color=color),
                    ft.Text(short_name, size=14, text_align="center", no_wrap=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            tooltip=item.name,
            on_click=lambda e, p=item: handle_click(p),
            padding=10,
            border_radius=8,
            data=item,
        )

        # Hover effect
        def on_hover(e):
            if selected_item["path"] != item:
                container.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREY_800) if e.data == "true" else "transparent"
                container.update()

        container.on_hover = on_hover
        return container

    def refresh():
        grid.controls.clear()
        path = current_path[0]
        back_button.visible = (path != BASE_DIR)
        update_breadcrumb()

        query = search_field.value.strip()

        if query:
            # Cancel previous search thread
            if search_thread["thread"] and search_thread["thread"].is_alive():
                return

            def do_search():
                results = search_all(BASE_DIR, query)
                content.page.call_from_thread(lambda: update_grid(results))

            t = threading.Thread(target=do_search, daemon=True)
            search_thread["thread"] = t
            t.start()
        else:
            folders, files = list_directory(path)
            for f in folders + files:
                grid.controls.append(build_item_tile(f))
            grid.update()
            back_button.update()

    def update_grid(results):
        grid.controls.clear()
        for item in results:
            grid.controls.append(build_item_tile(item))
        grid.update()

    search_field.on_change = lambda e: refresh()

    # ---------------- Top bar layout ----------------
    top_bar = ft.Row(
        [
            back_button,
            ft.ElevatedButton(icon=ft.Icons.UPLOAD, text="Upload"),
            ft.ElevatedButton(icon=ft.Icons.CREATE_NEW_FOLDER, text="New Folder"),
            breadcrumb,
            ft.Container(expand=True),
            search_field,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- Layout ---
    main_row = ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [
                        top_bar,
                        ft.Divider(),
                        ft.ListView(expand=True, controls=[grid]),  # Scroll only here
                    ],
                    expand=True,
                ),
                expand=3,
                margin=10,
            ),
            ft.VerticalDivider(width=1),
            ft.Container(content=details_panel, expand=1, alignment=ft.alignment.top_left, margin=10),
        ],
        expand=True,
    )

    # Add to page
    content.controls.append(main_row)
    content.update()

    refresh()
