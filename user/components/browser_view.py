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
        # Always show at least Program Files in breadcrumb
        self.breadcrumb_path = [BASE_DIR]  # Separate path for breadcrumb display
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

        # Create search field with integrated clear button
        self.clear_search_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            tooltip="Clear search",
            on_click=self.clear_search,
            visible=False,  # Hidden by default
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(2),
            )
        )
        
        self.search_field = ft.TextField(
            hint_text="Search...",
            width=350,
            height=44,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, ft.Colors.GREY)),
            prefix_icon=ft.Icons.SEARCH,
            suffix=self.clear_search_btn,
            on_submit=self.refresh,
            on_change=self.on_search_change,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            text_size=14,
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.6, ft.Colors.GREY),
                size=14
            ),
            cursor_color=ft.Colors.BLUE,
            focused_border_color=ft.Colors.BLUE,
        )

        # Load index on init - keep this as background task since it doesn't update UI
        threading.Thread(target=refresh_index, daemon=True).start()
        
        # Initialize breadcrumb immediately to show correct path
        self.update_breadcrumb()

    def set_navigation(self, navigation):
        self.navigation = navigation

    def show_loading(self, show: bool):
        """Disabled loading to prevent crashes and breadcrumb disappearing."""
        # No-op function - removed all loading functionality to prevent UI crashes
        pass

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
                    # Clear search when entering any directory (not just when going back)
                    self.clear_search_field()
                    self.current_path[0] = item
                    
                    # Update breadcrumb path only if entering Program Files tree
                    if self.is_in_program_files_tree(item):
                        self.breadcrumb_path[0] = item
                    # If navigating above Program Files, keep breadcrumb showing Program Files
                        
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
                try:
                    container.update()
                except:
                    pass  # Ignore update errors to prevent crashes

        container.on_hover = on_hover
        return container

    def highlight_selected(self):
        """Highlight selected item with better visual feedback."""
        try:
            for tile in self.grid.controls:
                if not hasattr(tile, 'data'):
                    continue
                path = tile.data
                if path == self.selected_item["path"]:
                    tile.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.BLUE)
                    tile.border = ft.border.all(2, ft.Colors.BLUE)
                else:
                    tile.bgcolor = "transparent"
                    tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                try:
                    tile.update()
                except:
                    pass  # Ignore individual update errors
        except Exception as ex:
            print(f"[ERROR] Highlight selection failed: {ex}")

    def show_details(self, item: Path):
        try:
            self.details_panel.update_details(item)
        except Exception as ex:
            print(f"[ERROR] Show details failed: {ex}")

    def deselect_all(self):
        try:
            self.selected_item["path"] = None
            for tile in self.grid.controls:
                if not hasattr(tile, 'bgcolor'):
                    continue
                tile.bgcolor = "transparent"
                tile.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                try:
                    tile.update()
                except:
                    pass  # Ignore individual update errors
            self.details_panel.clean()
        except Exception as ex:
            print(f"[ERROR] Deselect all failed: {ex}")

    def on_search_change(self, e):
        """Handle search field changes and show/hide clear button"""
        try:
            # Show/hide clear button based on whether there's text
            has_text = bool(e.control.value and e.control.value.strip())
            self.clear_search_btn.visible = has_text
            
            # Update the clear button
            if hasattr(self.clear_search_btn, 'page') and self.clear_search_btn.page:
                self.clear_search_btn.update()
                
            # Optionally trigger search on change (remove if you only want search on submit)
            # self.refresh()
            
        except Exception as ex:
            print(f"[ERROR] Search change handler failed: {ex}")

    def clear_search_field(self):
        """Helper method to properly clear the search field"""
        try:
            self.search_field.value = ""
            self.clear_search_btn.visible = False  # Hide clear button
            
            # Force UI update with error handling
            if hasattr(self.search_field, 'page') and self.search_field.page:
                self.search_field.update()
            if hasattr(self.clear_search_btn, 'page') and self.clear_search_btn.page:
                self.clear_search_btn.update()
        except Exception as ex:
            print(f"[ERROR] Clear search field failed: {ex}")

    def go_back(self, e=None):
        try:
            if self.current_path[0] != BASE_DIR:
                parent_path = self.current_path[0].parent
                
                # Clear search when going back to Program Files specifically
                if parent_path == BASE_DIR:
                    self.clear_search_field()
                
                self.current_path[0] = parent_path
                
                # Special rule: Keep Program Files visible in breadcrumb
                # Only update breadcrumb if we're still in Program Files tree
                if self.is_in_program_files_tree(self.current_path[0]):
                    self.breadcrumb_path[0] = self.current_path[0]
                # If going above Program Files, keep breadcrumb showing Program Files
                # (don't change breadcrumb_path)
                    
                self.refresh()
        except Exception as ex:
            print(f"[ERROR] Go back failed: {ex}")

    def update_breadcrumb(self):
        try:
            self.breadcrumb.controls.clear()
            # Use breadcrumb_path for display
            parts = list(self.breadcrumb_path[0].parts)
            
            for i, part in enumerate(parts):
                partial_path = Path(*parts[:i + 1])

                def create_breadcrumb_click(p):
                    def go_to_path(e):
                        try:
                            # Clear search when clicking on Program Files (BASE_DIR) specifically
                            if p == BASE_DIR:
                                self.clear_search_field()
                                
                            # Navigate to clicked path
                            self.current_path[0] = p
                            
                            # Special rule: Always keep "Program Files" visible in breadcrumb
                            # If clicking at Program Files level or deeper, truncate to that level
                            if self.is_in_program_files_tree(p):
                                self.breadcrumb_path[0] = p
                            else:  
                                # If clicking above Program Files (like C:\), keep showing Program Files
                                # but don't change the breadcrumb_path - just navigate
                                pass  # breadcrumb_path stays the same
                                
                            self.refresh()
                        except Exception as ex:
                            print(f"[ERROR] Breadcrumb click failed: {ex}")
                    return go_to_path

                # Enhanced breadcrumb styling
                # Highlight current location differently
                is_current = (partial_path == self.current_path[0])
                button_color = ft.Colors.BLUE if is_current else ft.Colors.BLACK
                
                self.breadcrumb.controls.append(
                    ft.TextButton(
                        text=part,
                        on_click=create_breadcrumb_click(partial_path),
                        style=ft.ButtonStyle(
                            color={
                                ft.ControlState.DEFAULT: button_color,
                                ft.ControlState.HOVERED: ft.Colors.GREY_800
                            },
                            text_style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.W_500
                            )
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
            # Safe breadcrumb update
            try:
                if hasattr(self.breadcrumb, 'page') and self.breadcrumb.page:
                    self.breadcrumb.update()
            except:
                pass  # Will be updated when page refreshes
        except Exception as ex:
            print(f"[ERROR] Breadcrumb update failed: {ex}")

    def is_in_program_files_tree(self, path):
        """Check if path is Program Files or deeper."""
        try:
            path.relative_to(BASE_DIR)
            return True
        except ValueError:
            return False

    def update_grid(self, items):
        """Safe grid update without crashes."""
        try:
            self.grid.controls.clear()
            for item in items:
                tile = self.build_tile(item)
                if tile:
                    self.grid.controls.append(tile)
            # Safe grid update
            try:
                if hasattr(self.grid, 'page') and self.grid.page:
                    self.grid.update()
            except:
                pass  # Will be updated when page refreshes
        except Exception as ex:
            print(f"[ERROR] Grid update failed: {ex}")

    def refresh(self, e=None):
        """Crash-free refresh that preserves breadcrumb."""
        # Always update breadcrumb first to show correct path
        self.update_breadcrumb()
        
        query = self.search_field.value.strip() if self.search_field.value else ""
        
        # Simple synchronous approach - no problematic UI updates
        try:
            results = []
            if query:
                results = search_all(query)
            else:
                results = sorted(self.current_path[0].iterdir())
            
            # Update grid without crashes
            self.update_grid(results)
            
        except Exception as ex:
            print(f"[ERROR] Refresh failed: {ex}")

    def clear_search(self, e=None):
        """Clear search and return to current directory."""
        try:
            self.clear_search_field()
            # Only update breadcrumb if we're in Program Files tree
            if self.is_in_program_files_tree(self.current_path[0]):
                self.breadcrumb_path[0] = self.current_path[0]
            # If current location is above Program Files, keep breadcrumb showing Program Files
            self.refresh()
        except Exception as ex:
            print(f"[ERROR] Clear search failed: {ex}")

    def create_toolbar(self):
        """Enhanced toolbar with proper alignment - single row layout."""
        
        # Back button
        back_btn = ft.IconButton(
            ft.Icons.ARROW_BACK, 
            tooltip="Back",
            on_click=self.go_back,
            icon_color=ft.Colors.GREY_700,
            icon_size=20,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                },
                shape=ft.CircleBorder(),
                padding=ft.padding.all(8)
            )
        )
        
        # Refresh button
        refresh_btn = ft.IconButton(
            ft.Icons.REFRESH, 
            tooltip="Refresh",
            on_click=self.refresh,
            icon_color=ft.Colors.GREY_700,
            icon_size=20,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                },
                shape=ft.CircleBorder(),
                padding=ft.padding.all(8)
            )
        )
        
        return ft.Container(
            content=ft.Column([
                # Single row with navigation buttons, breadcrumb, and search
                ft.Row(
                    [
                        # Left side - Navigation buttons and breadcrumb
                        ft.Row(
                            [
                                back_btn,
                                refresh_btn,
                                ft.Container(
                                    content=self.breadcrumb,
                                    margin=ft.margin.only(left=16)
                                )
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        
                        # Right side - Search field
                        ft.Container(
                            content=self.search_field,
                            alignment=ft.alignment.center_right
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ]),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.GREY),
        )

    def create_content(self):
        layout = ft.Column([
            # Toolbar with proper spacing
            self.create_toolbar(),
            
            # Main content area
            ft.Container(
                content=ft.Row([
                    # File grid area
                    ft.Container(
                        expand=True,
                        content=ft.GestureDetector(
                            on_tap=lambda e: self.deselect_all(),
                            content=self.grid
                        ),
                        padding=ft.padding.all(16)
                    ),
                    
                    # Divider
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.2, ft.Colors.GREY)),
                    
                    # Details panel
                    ft.Container(
                        content=self.details_panel,
                        width=300,
                        padding=ft.padding.all(16),
                        alignment=ft.alignment.top_left
                    )
                ], 
                expand=True,
                spacing=0
                ),
                expand=True
            ),
        ], 
        expand=True,
        spacing=0
        )

        # Safe initial loading - always show Program Files in breadcrumb
        try:
            # Initialize breadcrumb_path to show Program Files as minimum
            if self.is_in_program_files_tree(self.current_path[0]):
                self.breadcrumb_path[0] = self.current_path[0]
            else:
                # If starting above Program Files, show Program Files as minimum breadcrumb
                self.breadcrumb_path[0] = BASE_DIR
                
            self.update_breadcrumb()  # Ensure breadcrumb shows correct path
            results = sorted(self.current_path[0].iterdir())
            for item in results:
                tile = self.build_tile(item)
                if tile:
                    self.grid.controls.append(tile)
        except Exception as ex:
            print(f"[ERROR] Initial load failed: {ex}")
        
        return layout