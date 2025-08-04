import flet as ft
from flet import FontWeight
from typing import Optional
from pathlib import Path
import os
import time
import json
import threading
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog
from admin.details_pane import DetailsPane
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = get_base_dir()
INDEX_CACHE_PATH = Path("cache/index.json")

# Global index
global_file_index = []
index_lock = threading.Lock()

# Cache for search results
search_cache = {}
search_lock = threading.Lock()

SEARCH_DEBOUNCE = 0.3

# Overlay components
loading_overlay = None
loading_text = None


def post_to_main(page: ft.Page, fn):
    """Utility to run a function safely on the main thread."""
    page.add(ft.Text("", visible=False))
    fn()
    page.update()


def show_progress_overlay(page: ft.Page, show: bool, text: str = ""):
    """
    Show or hide a full-screen spinner overlay with percentage.
    """
    global loading_overlay, loading_text
    if loading_overlay is None:
        loading_text = ft.Text("", size=18, color=ft.Colors.WHITE, weight=FontWeight.BOLD)
        loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=80, height=80, stroke_width=5),
                    loading_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            visible=False,
            expand=True,
        )
        page.overlay.append(loading_overlay)

    loading_text.value = text
    loading_overlay.visible = show
    page.update()


def build_index_with_progress(base_dir: Path, page: ft.Page):
    """
    Scans BASE_DIR and builds an index while updating the progress overlay.
    """
    all_paths = []
    total_items = 0
    for _, dirs, files in os.walk(base_dir):
        total_items += len(dirs) + len(files)

    processed = 0
    start_time = time.time()
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            all_paths.append(str(Path(root) / d))
            processed += 1
            if processed % 50 == 0:
                percent = int(processed / max(total_items, 1) * 100)
                post_to_main(page, lambda p=percent: show_progress_overlay(page, True, f"Indexing... {p}%"))
        for f in files:
            all_paths.append(str(Path(root) / f))
            processed += 1
            if processed % 50 == 0:
                percent = int(processed / max(total_items, 1) * 100)
                post_to_main(page, lambda p=percent: show_progress_overlay(page, True, f"Indexing... {p}%"))

    elapsed = time.time() - start_time
    print(f"[DEBUG] Index built with {len(all_paths)} entries in {elapsed:.2f} seconds.")
    return all_paths


def save_index_to_cache():
    with index_lock:
        os.makedirs(INDEX_CACHE_PATH.parent, exist_ok=True)
        with open(INDEX_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(global_file_index, f)
    print("[DEBUG] Index saved to cache/index.json")


def load_index_from_cache():
    if INDEX_CACHE_PATH.exists():
        try:
            with open(INDEX_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[DEBUG] Loaded {len(data)} entries from cache/index.json")
                return data
        except Exception as e:
            print(f"[ERROR] Failed to load index cache: {e}")
    return []


def refresh_index(page=None):
    """
    Rebuild the index and display progress overlay.
    """
    global global_file_index
    start_time = time.time()

    def worker():
        post_to_main(page, lambda: show_progress_overlay(page, True, "Indexing... 0%"))
        idx = build_index_with_progress(BASE_DIR, page)
        with index_lock:
            global global_file_index
            global_file_index = idx
        save_index_to_cache()
        elapsed = time.time() - start_time
        print(f"[DEBUG] Index refreshed in {elapsed:.2f} seconds.")
        if page:
            def notify():
                show_progress_overlay(page, False)
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Index refreshed in {elapsed:.2f}s ({len(global_file_index)} entries)")
                )
                page.snack_bar.open = True
                page.update()

            post_to_main(page, notify)

    threading.Thread(target=worker, daemon=True).start()


class IndexWatcherHandler(FileSystemEventHandler):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.last_refresh = 0

    def on_any_event(self, event):
        now = time.time()
        if now - self.last_refresh > 2:
            print(f"[DEBUG] Detected change: {event.event_type} - {event.src_path}")
            self.last_refresh = now
            refresh_index(self.page)


def start_watcher(page):
    print(f"[DEBUG] Starting watchdog on {BASE_DIR}")
    event_handler = IndexWatcherHandler(page)
    observer = Observer()
    observer.schedule(event_handler, str(BASE_DIR), recursive=True)
    observer.daemon = True
    observer.start()
    return observer


def list_directory(path: Path):
    print(f"[DEBUG] Listing directory: {path}")
    folders = []
    files = []
    try:
        for item in sorted(path.iterdir()):
            if item.is_dir():
                folders.append(item)
            else:
                files.append(item)
    except Exception as e:
        print(f"[ERROR] Error listing directory {path}: {e}")
    return folders, files


def search_all(base: Path, query: str, max_results=500):
    print(f"[DEBUG] Searching index for '{query}'...")
    results = []
    q = query.lower()
    with index_lock:
        for path_str in global_file_index:
            if q in os.path.basename(path_str).lower():
                results.append(Path(path_str))
                if len(results) >= max_results:
                    print(f"[DEBUG] Max results reached ({max_results})")
                    break
    print(f"[DEBUG] Search completed with {len(results)} results.")
    return results


def data_management(content: ft.Column, username: Optional[str]):
    print("[DEBUG] Initializing data management UI")
    content.controls.clear()

    current_path = [BASE_DIR]
    selected_item = {"path": None}
    last_click_time = {"time": 0}
    search_thread = {"thread": None, "stop": False}
    page = content.page

    global global_file_index
    global_file_index = load_index_from_cache()
    if not global_file_index:
        refresh_index(page)

    start_watcher(page)

    grid = ft.GridView(
        expand=True,
        runs_count=6,
        max_extent=150,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
    )

    details_panel = DetailsPane()

    search_field = ft.TextField(
        hint_text="Search (press Enter)...",
        width=300,
        height=40,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
    )

    breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)

    back_button = ft.IconButton(
        ft.Icons.ARROW_BACK,
        tooltip="Back",
        on_click=lambda e: go_back(),
        visible=False,
    )

    def update_breadcrumb():
        breadcrumb.controls.clear()
        parts = list(current_path[0].parts)
        for i, part in enumerate(parts):
            partial_path = Path(*parts[: i + 1])

            def go_to_path(_, p=partial_path):
                current_path[0] = p
                refresh()

            breadcrumb.controls.append(
                ft.TextButton(
                    text=part,
                    on_click=go_to_path,
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: ft.Colors.BLUE}
                    ),
                )
            )
            if i < len(parts) - 1:
                breadcrumb.controls.append(ft.Text(">", weight=FontWeight.BOLD))

        breadcrumb.update()

    def show_details(item: Path):
        details_panel.update_details(item)

    def highlight_selected():
        for tile in grid.controls:
            path = tile.data
            tile.border = ft.border.all(2, ft.Colors.GREY_800) if path == selected_item["path"] else None
            tile.update()

    def open_item(item: Path):
        if item.is_dir():
            current_path[0] = item
            refresh()
        else:
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
        now = time.time()
        if selected_item["path"] != item or (now - last_click_time["time"]) > 0.5:
            selected_item["path"] = item
            last_click_time["time"] = now
            highlight_selected()
            show_details(item)
        else:
            open_item(item)
            selected_item["path"] = None
            refresh()

    def get_icon_and_color(item: Path):
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
        display_name = item.name
        max_len = 15
        short_name = display_name if len(display_name) <= max_len else display_name[: max_len - 3] + "..."

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

        def on_hover(e):
            if selected_item["path"] != item:
                container.bgcolor = (
                    ft.Colors.with_opacity(0.2, ft.Colors.GREY_800)
                    if e.data == "true"
                    else "transparent"
                )
                container.update()

        container.on_hover = on_hover
        return container

    def update_grid(results):
        grid.controls.clear()
        for item in results:
            grid.controls.append(build_item_tile(item))
        grid.update()

    def perform_search(query: str):
        with search_lock:
            if query in search_cache:
                update_grid(search_cache[query])
                return

        results = search_all(current_path[0], query)

        with search_lock:
            if not search_thread["stop"]:
                search_cache[query] = results
                post_to_main(page, lambda: update_grid(results))

    def refresh():
        path = current_path[0]
        back_button.visible = path != BASE_DIR
        update_breadcrumb()
        query = search_field.value.strip()

        if query:
            search_thread["stop"] = True
            if search_thread["thread"] and search_thread["thread"].is_alive():
                pass
            search_thread["stop"] = False

            def delayed_search():
                time.sleep(SEARCH_DEBOUNCE)
                if not search_thread["stop"]:
                    perform_search(query)

            t = threading.Thread(target=delayed_search, daemon=True)
            search_thread["thread"] = t
            t.start()
        else:
            folders, files = list_directory(path)
            update_grid(folders + files)
            back_button.update()

    def on_search_submit(e):
        refresh()

    search_field.on_submit = on_search_submit

    # --- UI Layout ---

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

    main_row = ft.Row(
        [
            ft.Container(
                content=ft.ListView(expand=True, controls=[grid]),
                expand=3,
                margin=10,
            ),
            ft.VerticalDivider(width=1),
            ft.Container(
                content=details_panel,
                expand=1,
                alignment=ft.alignment.top_left,
                margin=10,
            ),
        ],
        expand=True,
    )

    content.controls.append(
        ft.Column(
            [
                top_bar,
                ft.Divider(),
                main_row,
            ],
            expand=True,
        )
    )
    content.update()

    refresh()
