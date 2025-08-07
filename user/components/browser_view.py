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
    """Returns icon and color for files and folders."""
    if item.is_dir():
        return "FOLDER", "#FF9C07"  # Gold color for folders
    
    ext = item.suffix.lower()
    filename = item.name.lower()
    
    # Microsoft/Windows files
    if ext in [".msi", ".exe"]:
        return "APPS", "#0078D4"  # Microsoft Blue
    elif ext in [".dll", ".sys"]:
        return "SETTINGS", "#6B73FF"  # Purple
    elif "microsoft" in filename:
        return "BUSINESS", "#00BCF2"  # Light Blue
        
    # Document files
    elif ext == ".pdf":
        return "PICTURE_AS_PDF", "#FF4444"  # Red
    elif ext in [".doc", ".docx"]:
        return "DESCRIPTION", "#2B5CE6"  # Blue
    elif ext in [".txt", ".rtf"]:
        return "TEXT_SNIPPET", "#FF6B35"  # Orange
    elif ext in [".ppt", ".pptx"]:
        return "SLIDESHOW", "#D24726"  # Red-Orange
        
    # Spreadsheet files
    elif ext in [".xlsx", ".xls", ".csv"]:
        return "TABLE_CHART", "#34A853"  # Green
    
    # Image files
    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico"]:
        return "IMAGE", "#3497E2"  # Orange
    elif ext in [".psd", ".ai"]:
        return "BRUSH", "#FF3366"  # Pink
    
    # Video files
    elif ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv"]:
        return "MOVIE", "#9C27B0"  # Purple
    
    # Audio files
    elif ext in [".mp3", ".wav", ".flac", ".aac", ".wma"]:
        return "MUSIC_NOTE", "#E91E63"  # Pink
    
    # Archive files
    elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
        return "FOLDER_ZIP", "#FF9800"  # Orange
    
    # Code files
    elif ext in [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php"]:
        return "CODE", "#4CAF50"  # Green
    elif ext in [".json", ".xml", ".yaml", ".yml"]:
        return "DATA_OBJECT", "#9C27B0"  # Purple
    
    # CAD/Design files
    elif ext in [".icd", ".dwg", ".dxf"]:
        return "ARCHITECTURE", "#795548"  # Brown
        
    # Configuration files
    elif ext in [".ini", ".cfg", ".conf"]:
        return "TUNE", "#607D8B"  # Blue Gray
        
    # Log files
    elif ext in [".log", ".txt"] and ("log" in filename):
        return "ARTICLE", "#FF7043"  # Orange
        
    # Database files
    elif ext in [".db", ".sqlite", ".mdb"]:
        return "STORAGE", "#4DB6AC"  # Teal
        
    # Font files
    elif ext in [".ttf", ".otf", ".woff"]:
        return "FONT_DOWNLOAD", "#8E24AA"  # Purple
    
    # Default for unknown files - now more colorful!
    else:
        # Generate different colors based on first letter of filename
        first_char = filename[0] if filename else 'a'
        colors = [
            "#FF5722",  # Deep Orange
            "#E91E63",  # Pink
            "#9C27B0",  # Purple
            "#673AB7",  # Deep Purple
            "#3F51B5",  # Indigo
            "#2196F3",  # Blue
            "#00BCD4",  # Cyan
            "#009688",  # Teal
            "#4CAF50",  # Green
            "#8BC34A",  # Light Green
            "#CDDC39",  # Lime
            "#FFC107",  # Amber
            "#FF9800",  # Orange
            "#FF5722",  # Deep Orange
        ]
        color_index = ord(first_char) % len(colors)
        return "INSERT_DRIVE_FILE", colors[color_index]


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

        # Simplified loading overlay (rarely shown now)
        self.loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=30, height=30, stroke_width=3),
                    ft.Text("Loading...", size=14)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            visible=False,
            expand=True
        )

        if self.loading_overlay not in self.page.overlay:
            self.page.overlay.append(self.loading_overlay)

        # Load index on init - keep this as background task since it doesn't update UI
        threading.Thread(target=refresh_index, daemon=True).start()
        
        # Initialize breadcrumb immediately to show correct path
        self.update_breadcrumb()

    def set_navigation(self, navigation):
        self.navigation = navigation

    def show_loading(self, show: bool):
        """Simple loading display without timers."""
        self.loading_overlay.visible = show
        if self.page:
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
                    # Clear search when entering a directory
                    self.search_field.value = ""
                    self.current_path[0] = item
                    self.refresh()
                else:
                    def confirm_open():
                        try:
                            os.startfile(item)
                        except Exception as ex:
                            print(f"[ERROR] Could not open file: {ex}")

                    show_confirm_dialog(self.page, "Open File", f"Open '{item.name}'?", confirm_open)

        # Enhanced container with better hover effects
        container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(getattr(ft.Icons, icon), size=64, color=color),
                    ft.Text(
                        short_name, 
                        size=12, 
                        text_align="center", 
                        no_wrap=True,
                        weight=ft.FontWeight.W_500
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            tooltip=item.name,
            on_click=on_click_tile,
            padding=10,
            border_radius=10,
            data=item,
            bgcolor="transparent",
            border=ft.border.all(1, ft.Colors.TRANSPARENT)
        )

        def on_hover(e):
            if self.selected_item["path"] != item:
                if e.data == "true":
                    container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
                    container.border = ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.BLUE))
                else:
                    container.bgcolor = "transparent"
                    container.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                container.update()

        container.on_hover = on_hover
        return container

    def highlight_selected(self):
        """Highlight selected item with better visual feedback."""
        for tile in self.grid.controls:
            path = tile.data
            if path == self.selected_item["path"]:
                tile.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.BLUE)
                tile.border = ft.border.all(2, ft.Colors.BLUE)
            else:
                tile.bgcolor = "transparent"
                tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
            tile.update()

    def show_details(self, item: Path):
        self.details_panel.update_details(item)

    def deselect_all(self):
        self.selected_item["path"] = None
        for tile in self.grid.controls:
            tile.bgcolor = "transparent"
            tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
            tile.update()
        self.details_panel.clean()

    def go_back(self, e=None):
        if self.current_path[0] != BASE_DIR:
            # Clear search when going back
            self.search_field.value = ""
            self.current_path[0] = self.current_path[0].parent
            self.refresh()

    def update_breadcrumb(self):
        try:
            self.breadcrumb.controls.clear()
            parts = list(self.current_path[0].parts)
            for i, part in enumerate(parts):
                partial_path = Path(*parts[:i + 1])

                def create_breadcrumb_click(p):
                    def go_to_path(e):
                        # Clear search when clicking breadcrumb
                        self.search_field.value = ""
                        self.current_path[0] = p
                        self.refresh()
                    return go_to_path

                # Enhanced breadcrumb styling
                self.breadcrumb.controls.append(
                    ft.TextButton(
                        text=part,
                        on_click=create_breadcrumb_click(partial_path),
                        style=ft.ButtonStyle(
                            color={
                                ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                ft.ControlState.HOVERED: ft.Colors.GREY_800
                            },
                            text_style=ft.TextStyle(weight=ft.FontWeight.W_500)
                        )
                    )
                )
                if i < len(parts) - 1:
                    self.breadcrumb.controls.append(
                        ft.Text(
                            ">", 
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_600
                        )
                    )
            # Always try to update breadcrumb, handle page attachment gracefully
            try:
                if hasattr(self.breadcrumb, 'page') and self.breadcrumb.page:
                    self.breadcrumb.update()
            except:
                pass  # Breadcrumb will be updated when page is attached
        except Exception as ex:
            print(f"[ERROR] Breadcrumb update failed: {ex}")

    def update_grid(self, items):
        """Fast grid update without threading issues."""
        try:
            self.grid.controls.clear()
            for item in items:
                self.grid.controls.append(self.build_tile(item))
            if self.grid.page:  # Only update if grid is attached to page
                self.grid.update()
        except Exception as ex:
            print(f"[ERROR] Grid update failed: {ex}")

    def refresh(self, e=None):
        """Instant refresh - now synchronous to avoid threading issues."""
        # Always update breadcrumb first to show correct path
        self.update_breadcrumb()
        
        query = self.search_field.value.strip()
        
        # Simple synchronous approach - no threading issues
        try:
            results = []
            if query:
                results = search_all(query)
            else:
                results = sorted(self.current_path[0].iterdir())
            
            # Update UI directly on main thread
            self.update_grid(results)
            self.show_loading(False)
            
        except Exception as ex:
            print(f"[ERROR] Refresh failed: {ex}")
            self.show_loading(False)

    def clear_search(self, e=None):
        """Clear search and return to current directory."""
        self.search_field.value = ""
        self.refresh()

    def create_toolbar(self):
        """Enhanced toolbar with better styling."""
        return ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.ARROW_BACK, 
                        tooltip="Back",
                        on_click=self.go_back,
                        icon_color=ft.Colors.BLACK,
                        style=ft.ButtonStyle(
                            bgcolor={
                                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                            },
                            shape=ft.CircleBorder()
                        )
                    ),
                    margin=ft.margin.only(right=10)
                ),
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.REFRESH, 
                        tooltip="Refresh",
                        on_click=self.refresh,
                        icon_color=ft.Colors.BLACK,
                        style=ft.ButtonStyle(
                            bgcolor={
                                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                            },
                            shape=ft.CircleBorder()
                        )
                    ),
                    margin=ft.margin.only(right=10)
               
                ),
                ft.Container(
                    content=self.breadcrumb,
                    expand=True
                ),
                ft.Container(
                    content=self.search_field,
                    margin=ft.margin.only(left=10)
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def create_content(self):
        layout = ft.Column([
            ft.Container(
                content=self.create_toolbar(),
                padding=15,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY),
                border_radius=8
            ),
            ft.Row([
                ft.Container(
                    expand=True,
                    content=ft.GestureDetector(
                        on_tap=lambda e: self.deselect_all(),
                        content=self.grid
                    ),
                    margin=10
                ),
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                ft.Container(
                    content=self.details_panel,
                    width=300,
                    height=400,
                    alignment=ft.alignment.top_left,
                    margin=10,
                )
            ], expand=True),
        ], expand=True)

        # Initialize breadcrumb and load content immediately
        try:
            self.update_breadcrumb()  # Ensure breadcrumb shows correct path
            self.refresh()  # Load the files
        except Exception as ex:
            print(f"[ERROR] Initial load failed: {ex}")
        
        return layout