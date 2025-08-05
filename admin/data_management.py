import flet as ft
from flet import FontWeight
from typing import Optional
from pathlib import Path
import os
import time
import json
import shutil
import threading
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog, show_input_dialog
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

# Delay for debounce (in seconds)
SEARCH_DEBOUNCE = 0.3

# Reference for the loading overlay
loading_overlay = None
loading_text = None
loading_progress = None


# ---------------- Indexing and Watchdog ----------------

def show_loading_overlay(page: ft.Page, show: bool, progress: float = None):
    """
    Show or hide a full-screen spinner overlay with progress.
    """
    global loading_overlay, loading_text, loading_progress

    if loading_overlay is None:
        loading_progress = ft.ProgressBar(width=300, value=0)
        loading_text = ft.Text("Indexing...")
        loading_overlay = ft.Container(
            content=ft.Column(
                [
                    loading_text,
                    loading_progress,
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

    if progress is not None:
        loading_progress.value = progress
        loading_text.value = f"Indexing... {int(progress*100)}%"

    loading_overlay.visible = show
    page.update()


def build_index(base_dir: Path, page: Optional[ft.Page] = None):
    """
    Scans BASE_DIR and builds a list of all files and folders.
    Shows spinner while processing.
    """
    print(f"[DEBUG] Building index for {base_dir} ...")
    start_time = time.time()
    index = []

    # Count total for progress
    total_items = sum(len(files) + len(dirs) for _, dirs, files in os.walk(base_dir))
    processed = 0

    if page:
        show_loading_overlay(page, True, 0)

    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            index.append(str(Path(root) / d))
            processed += 1
        for f in files:
            index.append(str(Path(root) / f))
            processed += 1

        if page and total_items > 0:
            progress = processed / total_items
            show_loading_overlay(page, True, progress)

    elapsed = time.time() - start_time
    print(f"[DEBUG] Index built with {len(index)} entries in {elapsed:.2f} seconds.")

    if page:
        show_loading_overlay(page, False)

    return index


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
    Rebuilds index from disk and saves it to cache.
    """
    global global_file_index
    start_time = time.time()
    with index_lock:
        global_file_index = build_index(BASE_DIR, page)
    save_index_to_cache()
    elapsed = time.time() - start_time
    print(f"[DEBUG] Index refreshed in {elapsed:.2f} seconds.")
    if page:
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Index refreshed in {elapsed:.2f}s ({len(global_file_index)} entries)")
        )
        page.snack_bar.open = True
        page.update()


class IndexWatcherHandler(FileSystemEventHandler):
    """
    Handles file system events (create, delete, modify).
    """

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.last_refresh = 0

    def on_any_event(self, event):
        now = time.time()
        # Debounce: refresh at most once every 2 seconds
        if now - self.last_refresh > 2:
            print(f"[DEBUG] Detected change: {event.event_type} - {event.src_path}")
            self.last_refresh = now
            threading.Thread(target=lambda: refresh_index(self.page), daemon=True).start()


def start_watcher(page):
    """
    Starts a watchdog observer to monitor BASE_DIR.
    """
    print(f"[DEBUG] Starting watchdog on {BASE_DIR}")
    event_handler = IndexWatcherHandler(page)
    observer = Observer()
    observer.schedule(event_handler, str(BASE_DIR), recursive=True)
    observer.daemon = True
    observer.start()
    return observer


# ---------------- Directory Listing ----------------

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
    """
    Search in the in-memory global_file_index for speed.
    """
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


# ---------------- UI ----------------

def data_management(content: ft.Column, username: Optional[str]):
    print("[DEBUG] Initializing data management UI")
    content.controls.clear()

    current_path = [BASE_DIR]
    selected_item = {"path": None}
    last_click_time = {"time": 0}
    search_thread = {"thread": None, "stop": False}
    search_timer = {"timer": None}

    page = content.page

    global global_file_index
    global_file_index = load_index_from_cache()
    if not global_file_index:
        threading.Thread(target=lambda: refresh_index(page), daemon=True).start()

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
        hint_text="Search...",
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
        bgcolor= ft.Colors.BLACK,
        on_click=lambda e: go_back(),
        visible=False,
    )

     # Upload files
    def upload_files():
        def handle_files(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    dst = current_path[0] / Path(f.name).name
                    shutil.copy(f.path, dst)
                refresh()

        existing = next((c for c in page.overlay if isinstance(c, ft.FilePicker)), None)
        if existing:
            existing.on_result = handle_files
            existing.pick_files(allow_multiple=True)
        else:
            file_picker = ft.FilePicker(on_result=handle_files)
            page.overlay.append(file_picker)
            page.update()
            file_picker.pick_files(allow_multiple=True)

    # New folder
    def create_new_folder():
        def on_submit(name):
            if not name:
                return
            new = current_path[0] / name
            try:
                new.mkdir(exist_ok=False)
                refresh()
            except FileExistsError:
                page.snack_bar = ft.SnackBar(ft.Text("Folder already exists"), open=True)
                page.update()
            except PermissionError:
                page.snack_bar = ft.SnackBar(ft.Text("Permission denied: cannot create folder here"), open=True)
                page.update()


        show_input_dialog(page, "Create New Folder", "Folder name", on_submit)


    # ---------------- Core functions ----------------

    def update_breadcrumb():
        print(f"[DEBUG] Updating breadcrumb: {current_path[0]}")
        breadcrumb.controls.clear()
        parts = list(current_path[0].parts)
        for i, part in enumerate(parts):
            partial_path = Path(*parts[: i + 1])

            def go_to_path(_, p=partial_path):
                print(f"[DEBUG] Breadcrumb clicked: {p}")
                # Clear search bar before navigating
                if search_field.value.strip():
                    print("[DEBUG] Clearing search bar due to breadcrumb navigation")
                    search_field.value = ""
                    search_field.update()

                current_path[0] = p
                refresh()

            breadcrumb.controls.append(
                ft.TextButton(
                    text=part,
                    on_click=go_to_path,
                    style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: ft.Colors.BLACK}),
                )
            )
            if i < len(parts) - 1:
                breadcrumb.controls.append(ft.Text(">", weight=FontWeight.BOLD))

        breadcrumb.update()


    def show_details(item: Path):
        print(f"[DEBUG] Showing details for: {item}")
        details_panel.update_details(item)

    def highlight_selected():
        print(f"[DEBUG] Highlighting selection: {selected_item['path']}")
        for tile in grid.controls:
            path = tile.data
            if path == selected_item["path"]:
                tile.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREY_800)
            else:
                tile.bgcolor = "transparent"
            tile.update()

    def deselect_all():
        print("[DEBUG] Deselecting all items")
        selected_item["path"] = None
        for tile in grid.controls:
            tile.bgcolor = "transparent"
            tile.update()
        details_panel.clean()  # ← Use this instead of .clear()


    def open_item(item: Path):
        print(f"[DEBUG] Opening item: {item}")
        if item.is_dir():
            # If search bar has text, clear it before opening folder
            if search_field.value.strip():
                print("[DEBUG] Clearing search bar after folder open")
                search_field.value = ""
                search_field.update()

            current_path[0] = item
            refresh()
        else:
            def confirm_open():
                print(f"[DEBUG] Confirmed opening file: {item}")
                os.startfile(item)

            show_confirm_dialog(
                content.page,
                "Open File",
                f"Are you sure you want to open '{item.name}'?",
                confirm_open,
            )


    def go_back():
        if current_path[0] != BASE_DIR:
            # Clear search bar before going back
            if search_field.value.strip():
                search_field.value = ""
                search_field.update()

            current_path[0] = current_path[0].parent
            refresh()


    def handle_click(item: Path):
        now = time.time()
        print(f"[DEBUG] Item clicked: {item}")
        if selected_item["path"] != item or (now - last_click_time["time"]) > 0.5:
            selected_item["path"] = item
            last_click_time["time"] = now
            highlight_selected()
            show_details(item)
        else:
            print(f"[DEBUG] Double-click detected: {item}")
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
            return ft.Icons.ARCHITECTURE, "#990000"
        else:
            return ft.Icons.DESCRIPTION, "#000000"

    def build_item_tile(item: Path):
        icon, color = get_icon_and_color(item)
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

        def on_right_click(e):
            print(f"[DEBUG] Right-clicked on: {item}")

            def handle_refresh():
                print(f"[DEBUG] Refreshing...")
                refresh()

            def handle_rename():
                print(f"[DEBUG] Renaming: {item}")
                def on_submit(new_name):
                    if new_name:
                        new_path = item.parent / new_name
                        try:
                            item.rename(new_path)
                            refresh()
                        except Exception as ex:
                            page.snack_bar = ft.SnackBar(ft.Text(f"Rename failed: {ex}"), open=True)
                            page.update()
                show_input_dialog(page, "Rename", "New name:", on_submit)

            def handle_delete():
                print(f"[DEBUG] Deleting: {item}")
                def confirm():
                    try:
                        if item.is_dir():
                            os.rmdir(item)
                        else:
                            item.unlink()
                        refresh()
                    except Exception as ex:
                        page.snack_bar = ft.SnackBar(ft.Text(f"Delete failed: {ex}"), open=True)
                        page.update()
                show_confirm_dialog(
                    page,
                    "Delete Item",
                    f"Are you sure you want to delete '{item.name}'?",
                    confirm
                )

            # Build custom popup menu
            menu = ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="🌀 Refresh", on_click=lambda e: handle_refresh()),
                    ft.PopupMenuItem(text="✏️ Rename", on_click=lambda e: handle_rename()),
                    ft.PopupMenuItem(text="🗑️ Delete", on_click=lambda e: handle_delete()),
                ],
                tooltip="Options"
            )

            # Embed the popup in a container and show manually
            menu_container = ft.Container(content=menu, alignment=ft.alignment.top_left)
            page.overlay.append(menu_container)
            page.update()

            # Open the menu manually (needs short delay)
            def open_menu():
                menu.open = True
                page.update()
            threading.Timer(0.01, open_menu).start()

        container.on_secondary_tap = on_right_click  # right-click handler

        def on_hover(e):
            if selected_item["path"] != item:
                container.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREY_800) if e.data == "true" else "transparent"
                container.update()

        container.on_hover = on_hover
        return container



    def update_grid(results):
        print(f"[DEBUG] Updating grid with {len(results)} results")

        def do_update():
            grid.controls.clear()
            for item in results:
                grid.controls.append(build_item_tile(item))
            grid.update()

        # Call directly since we are now on main thread
        do_update()

    def perform_search(query: str):
        print(f"[DEBUG] perform_search: '{query}'")
        with search_lock:
            if query in search_cache:
                print(f"[DEBUG] Cache hit for query: '{query}'")
                cached_results = search_cache[query]
                update_grid(cached_results)
                return
            else:
                print(f"[DEBUG] Cache miss for query: '{query}'")

        # Perform search
        results = search_all(current_path[0], query)

        # Save results to cache and update UI (main thread)
        with search_lock:
            if not search_thread["stop"]:
                print(f"[DEBUG] Caching results for '{query}'")
                search_cache[query] = results
                update_grid(results)

    def refresh():
        print(f"[DEBUG] Refreshing UI for path: {current_path[0]}")
        grid.controls.clear()
        path = current_path[0]
        back_button.visible = (path != BASE_DIR)
        update_breadcrumb()

        query = search_field.value.strip()

        if query:
            print(f"[DEBUG] Refresh triggered search for '{query}'")
            # Cancel previous search
            search_thread["stop"] = True
            if search_thread["thread"] and search_thread["thread"].is_alive():
                pass
            search_thread["stop"] = False

            # Debounce
            def delayed_search():
                time.sleep(SEARCH_DEBOUNCE)
                if not search_thread["stop"]:
                    perform_search(query)

            t = threading.Thread(target=delayed_search, daemon=True)
            search_thread["thread"] = t
            t.start()
        else:
            folders, files = list_directory(path)
            for f in folders + files:
                grid.controls.append(build_item_tile(f))
            grid.update()
            back_button.update()

    def on_key_press(e: ft.KeyboardEvent):
        # Only trigger search when Enter is pressed
        if e.key == "Enter":
            refresh()

    search_field.on_submit = lambda e: refresh()
    page.on_keyboard_event = on_key_press

    # Add empty area click deselection
    def clear_selection_area_tap(e):
        deselect_all()

    blank_click_area = ft.Container(
        expand=True,
        on_click=clear_selection_area_tap,
        content=grid
    )

    top_bar = ft.Row(
        [
            back_button,
            ft.ElevatedButton(icon=ft.Icons.UPLOAD,
                              text="Upload",
                              on_click=lambda e: upload_files(),
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton(icon=ft.Icons.CREATE_NEW_FOLDER,
                              text="New Folder",
                              on_click=lambda e: create_new_folder(),
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            breadcrumb,
            ft.Container(expand=True),
            search_field,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    blank_click_area = ft.Container(
        expand=True,
        on_click=lambda e: deselect_all(),
        content=grid
    )

    main_row = ft.Column(
        [
            ft.Container(
                content=top_bar,
                padding=10,
                expand=False,
            ),
            ft.Divider(),
            ft.Row(
                [
                    ft.Column(
                        [blank_click_area],
                        expand=3,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=details_panel,
                        width=300,
                        height=400,
                        alignment=ft.alignment.top_left,
                        margin=10,
                    ),
                ],
                expand=True,
            )
        ],
        expand=True,
    )

    content.controls.append(main_row)
    content.update()
    refresh()
