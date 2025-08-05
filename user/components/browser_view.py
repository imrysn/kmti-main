import flet as ft
import os
import time
import threading
from pathlib import Path
from typing import Optional
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog
from admin.details_pane import DetailsPane

BASE_DIR = get_base_dir()
global_file_index = []
index_lock = threading.Lock()
search_cache = {}
search_lock = threading.Lock()
SEARCH_DEBOUNCE = 0.3


def build_index(base_dir: Path):
    index = []
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            index.append(str(Path(root) / d))
        for f in files:
            index.append(str(Path(root) / f))
    return index


def refresh_index():
    global global_file_index
    with index_lock:
        global_file_index = build_index(BASE_DIR)


def search_all(query: str, max_results=500):
    results = []
    q = query.lower()
    with index_lock:
        for path_str in global_file_index:
            if q in os.path.basename(path_str).lower():
                results.append(Path(path_str))
                if len(results) >= max_results:
                    break
    return results


def get_icon_and_color(item: Path):
    if item.is_dir():
        return "FOLDER", "#000000"
    ext = item.suffix.lower()
    if ext == ".pdf":
        return "PICTURE_AS_PDF", "red"
    elif ext in [".xlsx", ".xls"]:
        return "TABLE_CHART", "green"
    elif ext in [".zip", ".rar"]:
        return "FOLDER_ZIP", "orange"
    elif ext in [".icd", ".dwg"]:
        return "ARCHITECTURE", "#990000"
    else:
        return "DESCRIPTION", "#000000"


class BrowserView:
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
        self.navigation = None

        self.current_path = [BASE_DIR]
        self.selected_item = {"path": None}
        self.last_click_time = {"time": 0}

        self.details_panel = DetailsPane()
        self.breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)

        self.grid = ft.GridView(
            expand=True,
            runs_count=6,
            max_extent=150,
            child_aspect_ratio=0.8,
            spacing=10,
            run_spacing=10,
        )

        self.search_field = ft.TextField(
            hint_text="Search...",
            width=300,
            height=40,
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self.refresh
        )

        self.loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Loading...", size=16),
                    ft.ProgressBar(width=300, value=None)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            visible=False,
            expand=True
        )

        if self.loading_overlay not in self.page.overlay:
            self.page.overlay.append(self.loading_overlay)

        self.search_thread = None
        self.search_stop = False

        # Load index on init
        threading.Thread(target=refresh_index, daemon=True).start()

    def set_navigation(self, navigation):
        self.navigation = navigation

    def show_loading(self, show: bool):
        self.loading_overlay.visible = show
        self.page.update()

    def build_tile(self, item: Path):
        icon, color = get_icon_and_color(item)
        display_name = item.name
        short_name = display_name if len(display_name) <= 15 else display_name[:12] + "..."

        def on_click_tile(e):
            now = time.time()
            if self.selected_item["path"] != item or (now - self.last_click_time["time"]) > 0.5:
                self.selected_item["path"] = item
                self.last_click_time["time"] = now
                self.highlight_selected()
                self.show_details(item)
            else:
                if item.is_dir():
                    self.current_path[0] = item
                    self.refresh()
                else:
                    def confirm_open():
                        try:
                            os.startfile(item)
                        except Exception as ex:
                            print(f"[ERROR] Could not open file: {ex}")

                    show_confirm_dialog(self.page, "Open File", f"Open '{item.name}'?", confirm_open)

        container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(getattr(ft.Icons, icon), size=64, color=color),
                    ft.Text(short_name, size=14, text_align="center", no_wrap=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            tooltip=item.name,
            on_click=on_click_tile,
            padding=10,
            border_radius=8,
            data=item,
            bgcolor="transparent"
        )

        def on_hover(e):
            if self.selected_item["path"] != item:
                container.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREY_800) if e.data == "true" else "transparent"
                container.update()

        container.on_hover = on_hover
        return container

    def highlight_selected(self):
        for tile in self.grid.controls:
            path = tile.data
            tile.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREY_800) if path == self.selected_item["path"] else "transparent"
            tile.update()

    def show_details(self, item: Path):
        self.details_panel.update_details(item)

    def deselect_all(self):
        self.selected_item["path"] = None
        for tile in self.grid.controls:
            tile.bgcolor = "transparent"
            tile.update()
        self.details_panel.clean()

    def go_back(self, e=None):
        if self.current_path[0] != BASE_DIR:
            self.current_path[0] = self.current_path[0].parent
            self.refresh()

    def update_breadcrumb(self):
        if self.breadcrumb.page is None:
            return
        self.breadcrumb.controls.clear()
        parts = list(self.current_path[0].parts)
        for i, part in enumerate(parts):
            partial_path = Path(*parts[:i + 1])

            def go_to_path(_, p=partial_path):
                self.current_path[0] = p
                self.refresh()

            self.breadcrumb.controls.append(
                ft.TextButton(
                    text=part,
                    on_click=go_to_path,
                    style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: ft.Colors.BLACK})
                )
            )
            if i < len(parts) - 1:
                self.breadcrumb.controls.append(ft.Text(">", weight=ft.FontWeight.BOLD))
        self.breadcrumb.update()

    def update_grid(self, items):
        self.grid.controls.clear()
        for item in items:
            self.grid.controls.append(self.build_tile(item))
        self.grid.update()

    def refresh(self, e=None):
        self.show_loading(True)
        self.update_breadcrumb()
        query = self.search_field.value.strip()

        def run_search():
            time.sleep(SEARCH_DEBOUNCE)
            if self.search_stop:
                return
            results = []
            if query:
                results = search_all(query)
            else:
                try:
                    results = sorted(self.current_path[0].iterdir())
                except Exception as ex:
                    print(f"[ERROR] Cannot read dir: {ex}")
            self.page.controls.append(ft.Container())  # Force UI update trigger
            self.update_grid(results)
            self.show_loading(False)

        self.search_stop = True
        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.join()
        self.search_stop = False
        self.search_thread = threading.Thread(target=run_search, daemon=True)
        self.search_thread.start()

    def create_toolbar(self):
        return ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Back", on_click=self.go_back),
                self.breadcrumb,
                ft.Container(expand=True),
                self.search_field,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def create_content(self):
        layout = ft.Column([
            ft.Container(content=self.create_toolbar(), padding=10),
            ft.Divider(),
            ft.Row([
                ft.Container(
                    expand=True,
                    content=ft.GestureDetector(
                        on_tap=lambda e: self.deselect_all(),
                        content=self.grid
                    )
                ),
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=self.details_panel,
                    width=300,
                    height=400,
                    alignment=ft.alignment.top_left,
                    margin=10,
                )
            ], expand=True),
        ], expand=True)

        threading.Timer(0.05, self.refresh).start()
        return layout
