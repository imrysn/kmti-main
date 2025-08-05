import flet as ft
from flet import FontWeight
from typing import Optional, List, Dict, Set
from pathlib import Path
import os
import time
import json
import shutil
import threading
from flet import Colors
from collections import defaultdict
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog, show_input_dialog
from admin.details_pane import DetailsPane

BASE_DIR = get_base_dir()
INDEX_CACHE_PATH = Path("cache/index.json")

# ===== SIMPLIFIED SEARCH ENGINE =====
class SimpleSearchEngine:
    def __init__(self):
        self.file_paths: List[Path] = []
        self.search_cache: Dict[str, List[Path]] = {}
        self.index_lock = threading.RLock()
        self.cache_lock = threading.RLock()
        self.is_indexing = False
        
    def build_index(self, base_dir: Path, progress_callback=None) -> List[Path]:
        """Build simple file path index"""
        print(f"[DEBUG] Building simple index for {base_dir}")
        self.is_indexing = True
        start_time = time.time()
        
        paths = []
        
        try:
            # Count total items for progress
            total_items = 0
            for root, dirs, files in os.walk(base_dir):
                total_items += len(dirs) + len(files)
            
            processed = 0
            
            for root, dirs, files in os.walk(base_dir):
                root_path = Path(root)
                
                # Process directories
                for d in dirs:
                    try:
                        dir_path = root_path / d
                        if dir_path.exists():
                            paths.append(dir_path)
                        processed += 1
                    except Exception as e:
                        print(f"[WARNING] Failed to process directory {d}: {e}")
                
                # Process files
                for f in files:
                    try:
                        file_path = root_path / f
                        if file_path.exists():
                            paths.append(file_path)
                        processed += 1
                    except Exception as e:
                        print(f"[WARNING] Failed to process file {f}: {e}")
                
                # Update progress
                if progress_callback and total_items > 0:
                    progress = processed / total_items
                    progress_callback(progress)
                    
        except Exception as e:
            print(f"[ERROR] Index building failed: {e}")
        
        elapsed = time.time() - start_time
        print(f"[DEBUG] Simple index built: {len(paths)} items in {elapsed:.2f}s")
        
        with self.index_lock:
            self.file_paths = paths
        
        self.is_indexing = False
        return paths
    
    def search(self, query: str, max_results: int = 200) -> List[Path]:
        """Simple search implementation"""
        if not query:
            return []
        
        # Check cache
        cache_key = f"{query}_{max_results}"
        with self.cache_lock:
            if cache_key in self.search_cache:
                return self.search_cache[cache_key]
        
        query_lower = query.lower()
        results = []
        
        with self.index_lock:
            for path in self.file_paths:
                try:
                    if query_lower in path.name.lower():
                        results.append(path)
                        if len(results) >= max_results:
                            break
                except Exception:
                    continue
        
        # Cache results
        with self.cache_lock:
            self.search_cache[cache_key] = results
            
        return results

# Global search engine
search_engine = SimpleSearchEngine()

# ===== MAIN DATA MANAGEMENT FUNCTION =====
def data_management(content: ft.Column, username: Optional[str]):
    print("[DEBUG] Initializing simple data management UI")
    content.controls.clear()
    
    # State management
    current_path = [BASE_DIR]
    selected_item = {"path": None}
    last_click_time = {"time": 0}
    current_search_thread = None
    search_stop_event = threading.Event()
    
    page = content.page
    
    # ===== INITIALIZE SEARCH ENGINE =====
    def initialize_search():
        def build_fresh_index():
            def progress_callback(progress):
                if hasattr(page, 'snack_bar'):
                    page.snack_bar = ft.SnackBar(
                        ft.Text(f"Indexing... {int(progress*100)}%"),
                        open=True
                    )
                    page.update()
            
            search_engine.build_index(BASE_DIR, progress_callback)
            print("[DEBUG] Index building completed")
        
        threading.Thread(target=build_fresh_index, daemon=True).start()
    
    # ===== UI COMPONENTS =====
    grid = ft.GridView(
        expand=True,
        runs_count=8,
        max_extent=140,
        child_aspect_ratio=0.9,
        spacing=12,
        run_spacing=12,
    )
    
    details_panel = DetailsPane()
    breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)
    
    # Status bar
    status_bar = ft.Container(
        content=ft.Row([
            ft.Text("Ready", size=12, color=ft.Colors.GREY_700),
            ft.Container(expand=True),
            ft.Text("0 items", size=12, color=ft.Colors.GREY_700),
        ]),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        bgcolor=ft.Colors.GREY_100,
        border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8)
    )
    
    # Search field
    search_field = ft.TextField(
        hint_text="Search files and folders...",
        width=350,
        height=40,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: perform_search(e.control.value.strip()),
        on_change=lambda e: handle_search_change(e.control.value.strip())
    )
    
    # ===== CORE FUNCTIONS =====
    def get_enhanced_icon_and_color(item: Path):
        """Get enhanced Icons and Colors"""
        if item.is_dir():
            return ft.Icons.FOLDER, "#FFC107"
        
        ext = item.suffix.lower()
        
        # Enhanced file type detection
        icon_map = {
            # Documents
            '.pdf': (ft.Icons.PICTURE_AS_PDF, "#D32F2F"),
            '.doc': (ft.Icons.DESCRIPTION, "#1976D2"),
            '.docx': (ft.Icons.DESCRIPTION, "#1976D2"),
            '.txt': (ft.Icons.TEXT_SNIPPET, "#616161"),
            
            # Spreadsheets
            '.xls': (ft.Icons.TABLE_CHART, "#0F9D58"),
            '.xlsx': (ft.Icons.TABLE_CHART, "#0F9D58"),
            
            # Images
            '.jpg': (ft.Icons.IMAGE, "#4CAF50"),
            '.jpeg': (ft.Icons.IMAGE, "#4CAF50"),
            '.png': (ft.Icons.IMAGE, "#4CAF50"),
            '.gif': (ft.Icons.IMAGE, "#FF5722"),
            
            # Videos
            '.mp4': (ft.Icons.MOVIE, "#E91E63"),
            '.avi': (ft.Icons.MOVIE, "#E91E63"),
            '.mkv': (ft.Icons.MOVIE, "#E91E63"),
            
            # Archives
            '.zip': (ft.Icons.FOLDER_ZIP, "#FF9800"),
            '.rar': (ft.Icons.FOLDER_ZIP, "#FF9800"),
            
            # Code files
            '.py': (ft.Icons.CODE, "#3776AB"),
            '.js': (ft.Icons.CODE, "#F7DF1E"),
            '.html': (ft.Icons.CODE, "#E34F26"),
        }
        
        return icon_map.get(ext, (ft.Icons.INSERT_DRIVE_FILE, "#757575"))
    
    def build_enhanced_tile(item: Path):
        """Build enhanced item tile with better styling"""
        icon, color = get_enhanced_icon_and_color(item)
        display_name = item.name
        short_name = display_name if len(display_name) <= 14 else display_name[:11] + "..."
        
        def on_click_tile(e):
            handle_item_click(item)
        
        # Enhanced tile with modern styling
        container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, size=48, color=color),
                    padding=5
                ),
                ft.Container(
                    content=ft.Text(
                        short_name,
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        weight=ft.FontWeight.W_500
                    ),
                    padding=ft.padding.symmetric(horizontal=4),
                    height=35
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
            tooltip=item.name,
            on_click=on_click_tile,
            padding=8,
            border_radius=12,
            data=item,
            bgcolor="transparent",
            border=ft.border.all(1, ft.Colors.TRANSPARENT)
        )
        
        def on_hover(e):
            if selected_item["path"] != item:
                if e.data == "true":
                    container.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.BLUE)
                    container.border = ft.border.all(1.5, ft.Colors.BLUE_300)
                else:
                    container.bgcolor = "transparent"
                    container.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                container.update()
        
        container.on_hover = on_hover
        return container
    
    def handle_item_click(item: Path):
        """Handle item click with double-click detection"""
        now = time.time()
        
        if selected_item["path"] != item or (now - last_click_time["time"]) > 0.5:
            # Single click - select item
            selected_item["path"] = item
            last_click_time["time"] = now
            highlight_selected()
            show_details(item)
        else:
            # Double click - open item
            open_item(item)
    
    def open_item(item: Path):
        """Open file or navigate to directory"""
        if item.is_dir():
            # Clear search when navigating
            search_field.value = ""
            current_path[0] = item
            refresh_directory()
            if search_field.page:
                search_field.update()
        else:
            def confirm_open():
                try:
                    os.startfile(item)
                except Exception as e:
                    page.snack_bar = ft.SnackBar(
                        ft.Text(f"Failed to open file: {e}"),
                        open=True
                    )
                    page.update()
            
            show_confirm_dialog(
                page,
                "Open File",
                f"Open '{item.name}'?",
                confirm_open
            )
    
    def highlight_selected():
        """Highlight selected item"""
        for tile in grid.controls:
            path = tile.data
            if path == selected_item["path"]:
                tile.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.BLUE)
                tile.border = ft.border.all(2, ft.Colors.BLUE)
            else:
                tile.bgcolor = "transparent"
                tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
            tile.update()
    
    def show_details(item: Path):
        """Show item details"""
        details_panel.update_details(item)
    
    def deselect_all():
        """Deselect all items"""
        selected_item["path"] = None
        for tile in grid.controls:
            tile.bgcolor = "transparent"
            tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
            tile.update()
        details_panel.clean()
    
    def update_breadcrumb():
        """Update breadcrumb navigation"""
        breadcrumb.controls.clear()
        parts = list(current_path[0].parts)
        
        for i, part in enumerate(parts):
            partial_path = Path(*parts[:i + 1])
            
            def go_to_path(_, p=partial_path):
                search_field.value = ""
                current_path[0] = p
                refresh_directory()
                if search_field.page:
                    search_field.update()
            
            breadcrumb.controls.append(
                ft.TextButton(
                    text=part,
                    on_click=go_to_path,
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: ft.Colors.BLUE_800}
                    )
                )
            )
            
            if i < len(parts) - 1:
                breadcrumb.controls.append(
                    ft.Text("›", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
                )
        
        if breadcrumb.page:
            breadcrumb.update()
    
    def update_grid(items: List[Path]):
        """Update grid with items"""
        grid.controls.clear()
        
        # Limit items for performance
        display_items = items[:200] if len(items) > 200 else items
        
        for item in display_items:
            try:
                if item.exists():  # Check if path still exists
                    grid.controls.append(build_enhanced_tile(item))
            except Exception as e:
                print(f"[WARNING] Skipping invalid item: {e}")
                continue
        
        if grid.page:
            grid.update()
        
        # Update status
        status_text = f"{len(display_items)} of {len(items)} items"
        if len(items) > 200:
            status_text += " (showing first 200)"
        
        status_bar.content.controls[2].value = status_text
        if status_bar.page:
            status_bar.update()
    
    def handle_search_change(query: str):
        """Handle search input changes with debouncing"""
        # Cancel previous search
        search_stop_event.set()
        
        if not query:
            refresh_directory()
            return
        
        if len(query) < 3:
            return
        
        # Debounced search
        def delayed_search():
            time.sleep(0.5)  # Debounce delay
            if not search_stop_event.is_set():
                perform_search(query)
        
        search_stop_event.clear()
        threading.Thread(target=delayed_search, daemon=True).start()
    
    def perform_search(query: str):
        """Perform search"""
        if not query:
            refresh_directory()
            return
        
        # Cancel previous search
        search_stop_event.set()
        
        def search_worker():
            try:
                # Update status
                status_bar.content.controls[0].value = f"Searching for '{query}'..."
                if status_bar.page:
                    status_bar.update()
                
                # Perform search
                results = search_engine.search(query, max_results=500)
                
                if not search_stop_event.is_set():
                    # Update UI
                    update_grid(results)
                    
                    # Update status
                    status_bar.content.controls[0].value = f"Found {len(results)} results"
                    if status_bar.page:
                        status_bar.update()
                
            except Exception as e:
                print(f"[ERROR] Search failed: {e}")
                status_bar.content.controls[0].value = "Search failed"
                if status_bar.page:
                    status_bar.update()
        
        search_stop_event.clear()
        threading.Thread(target=search_worker, daemon=True).start()
    
    def refresh_directory():
        """Refresh current directory"""
        update_breadcrumb()
        
        def load_directory():
            try:
                items = sorted(current_path[0].iterdir())
                update_grid(items)
                
                status_bar.content.controls[0].value = "Ready"
                if status_bar.page:
                    status_bar.update()
                    
            except Exception as e:
                print(f"[ERROR] Cannot read directory: {e}")
                status_bar.content.controls[0].value = "Error reading directory"
                if status_bar.page:
                    status_bar.update()
        
        threading.Thread(target=load_directory, daemon=True).start()
    
    def refresh_current_view():
        """Refresh current view (search or directory)"""
        query = search_field.value.strip()
        if query:
            perform_search(query)
        else:
            refresh_directory()
    
    def go_back(e=None):
        """Navigate back"""
        if current_path[0] != BASE_DIR:
            search_field.value = ""
            current_path[0] = current_path[0].parent
            refresh_directory()
            if search_field.page:
                search_field.update()
    
    def upload_files(e=None):
        """Upload files to current directory"""
        def handle_files(e: ft.FilePickerResultEvent):
            if e.files:
                upload_count = 0
                for f in e.files:
                    try:
                        dst = current_path[0] / Path(f.name).name
                        shutil.copy(f.path, dst)
                        upload_count += 1
                    except Exception as ex:
                        print(f"[ERROR] Upload failed for {f.name}: {ex}")
                
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Uploaded {upload_count} files"),
                    open=True
                )
                page.update()
                
                refresh_current_view()
        
        # Use existing file picker or create new one
        existing = next((c for c in page.overlay if isinstance(c, ft.FilePicker)), None)
        if existing:
            existing.on_result = handle_files
            existing.pick_files(allow_multiple=True)
        else:
            file_picker = ft.FilePicker(on_result=handle_files)
            page.overlay.append(file_picker)
            page.update()
            file_picker.pick_files(allow_multiple=True)
    
    def create_new_folder(e=None):
        """Create new folder"""
        def on_submit(name):
            if not name:
                return
            
            try:
                new_folder = current_path[0] / name
                new_folder.mkdir(exist_ok=False)
                refresh_current_view()
                
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Folder '{name}' created"),
                    open=True
                )
                page.update()
                
            except FileExistsError:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Folder already exists"),
                    open=True
                )
                page.update()
            except Exception as e:
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Failed to create folder: {e}"),
                    open=True
                )
                page.update()
        
        show_input_dialog(page, "Create New Folder", "Folder name:", on_submit)
    
    # ===== KEYBOARD SHORTCUTS =====
    def handle_keyboard(e: ft.KeyboardEvent):
        if e.key == "F5":
            refresh_current_view()
        elif e.key == "F" and e.ctrl:
            search_field.focus()
    
    page.on_keyboard_event = handle_keyboard
    
    # ===== LAYOUT =====
    toolbar = ft.Container(
        content=ft.Row([
            # Navigation buttons
            ft.IconButton(
                ft.Icons.ARROW_BACK,
                tooltip="Back (Alt+Left)",
                on_click=go_back,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.HOVERED: ft.Colors.GREY_200}
                )
            ),
            ft.IconButton(
                ft.Icons.REFRESH,
                tooltip="Refresh (F5)",
                on_click=lambda e: refresh_current_view(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.HOVERED: ft.Colors.GREY_200}
                )
            ),
            
            # Action buttons
            ft.ElevatedButton(
                "📤 Upload",
                icon=ft.Icons.UPLOAD,
                on_click=upload_files,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE},
                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                )
            ),
            ft.ElevatedButton(
                "📁 New Folder",
                icon=ft.Icons.CREATE_NEW_FOLDER,
                on_click=create_new_folder,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN},
                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                )
            ),
            
            # Spacer
            ft.Container(width=20),
            
            # Breadcrumb
            breadcrumb,
            
            # Right spacer
            ft.Container(expand=True),
            
            # Search field
            search_field,
            
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border_radius=ft.border_radius.only(top_left=8, top_right=8)
    )
    
    main_content = ft.Row([
        # Main grid area
        ft.Column([
            ft.Container(
                expand=True,
                content=ft.GestureDetector(
                    on_tap=lambda e: deselect_all(),
                    content=grid
                )
            ),
        ], expand=3),
        
        ft.VerticalDivider(width=1),
        
        # Details panel
        ft.Container(
            content=details_panel,
            width=320,
            alignment=ft.alignment.top_left,
        ),
    ], expand=True)
    
    # Complete layout
    layout = ft.Column([
        toolbar,
        ft.Divider(height=1),
        main_content,
        status_bar,
    ], expand=True, spacing=0)
    
    content.controls.append(layout)
    content.update()
    
    # Initialize everything
    initialize_search()
    refresh_directory()
    
    print("[DEBUG] Simple data management UI initialized")