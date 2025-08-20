import flet as ft
import os
import time
import threading
import shutil
from pathlib import Path
from typing import Optional, List
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog
from admin.components.details_pane import DetailsPane

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
        return "IMAGE", "#3497E2"  # Blue
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
    
    # Default for unknown files
    else:
        first_char = filename[0] if filename else 'a'
        colors = [
            "#FF5722", "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#2196F3",
            "#00BCD4", "#009688", "#4CAF50", "#8BC34A", "#CDDC39", "#FFC107",
            "#FF9800", "#FF5722"
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
        self.selected_items = set()  # Support multiple selection
        self.last_click_time = {"time": 0}
        self.clipboard_items = []  # For cut/copy operations
        self.clipboard_operation = None  # 'cut' or 'copy'
        self.view_mode = "grid"  # 'grid' or 'list'
        self.sort_by = "name"  # 'name', 'size', 'date', 'type'
        self.sort_ascending = True
        self.details_panel = DetailsPane()
        self.breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)
        
        # Store references to UI components for dynamic updates
        self.back_button = None
        self.toolbar_container = None
        self.main_layout = None

        # Grid and List views - BIGGER GRID
        self.grid = ft.GridView(
            expand=True,
            runs_count=5,  # Reduced from 6 to 5 to make tiles bigger
            max_extent=180,  # Increased from 150 to 180
            child_aspect_ratio=0.8,
            spacing=12,  # Increased from 10 to 12
            run_spacing=12,  # Increased from 10 to 12
        )
        
        self.list_view = ft.ListView(
            expand=True,
            spacing=4,  # Increased from 2 to 4 for better separation between rows
        )

        # Create search field
        self.clear_search_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            tooltip="Clear search",
            on_click=self.clear_search,
            visible=False,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(2),
            )
        )
        
        self.search_field = ft.TextField(
            hint_text="Search files and folders...",
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
        )

        # Address bar for direct path input
        self.address_bar = ft.TextField(
            hint_text="Enter path...",
            border_radius=8,
            height=36,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_submit=self.navigate_to_path,
            text_size=13,
            visible=False,  # Hidden by default, shown when clicking on breadcrumb
        )

        # Context menu items
        self.context_menu_items = []

        # Status bar
        self.status_text = ft.Text("Ready", size=12, color=ft.Colors.GREY_700)
        
        # Load index on init
        threading.Thread(target=refresh_index, daemon=True).start()
        self.update_breadcrumb()

    def set_navigation(self, navigation):
        """Set navigation reference and ensure proper initialization"""
        self.navigation = navigation
        # Ensure view is properly initialized when navigation is set
        if hasattr(self, 'current_path') and self.current_path:
            self.on_panel_activated()

    def go_back(self, e=None):
        """Navigate to parent directory - WITH IMMEDIATE UI UPDATE"""
        try:
            print("[INFO] Go back requested")
            
            # Ensure we have a valid current path
            if not self.current_path or not self.current_path[0]:
                print("[WARNING] No current path, cannot go back")
                self.show_status("Cannot go back - invalid current location")
                return
                
            current = self.current_path[0]
            
            # Validate current path still exists
            if not current.exists():
                print(f"[WARNING] Current path {current} no longer exists")
                self.show_status("Current location no longer exists")
                # Reset to base directory
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
                self.force_ui_refresh()
                return
            
            # Check if we can actually go back
            try:
                parent_path = current.parent
                # Check if parent exists and is different from current
                if not parent_path.exists() or parent_path == current:
                    self.show_status("Cannot go back further")
                    return
                    
                # Check if parent is accessible
                if not os.access(parent_path, os.R_OK):
                    self.show_status("Cannot access parent directory")
                    return
                    
            except (OSError, ValueError):
                self.show_status("Cannot go back further") 
                return
            
            print(f"[INFO] Navigating from {current} to {parent_path}")
            
            # Clear search when going back to Program Files specifically
            if parent_path == BASE_DIR:
                self.clear_search_field()
            
            # Update current path
            self.current_path[0] = parent_path
            
            # Update breadcrumb path - keep in sync
            self.breadcrumb_path[0] = parent_path
                    
            # Clear selection when navigating
            self.selected_items.clear()
            
            # IMMEDIATELY update back button state
            self.update_back_button_state()
            
            # Refresh view
            self.refresh()
            self.show_status(f"Navigated to {parent_path}")
                
        except Exception as ex:
            self.show_status(f"Cannot navigate back: {ex}")
            print(f"[ERROR] Go back failed: {ex}")
            
            # Emergency fallback
            try:
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
                self.force_ui_refresh()
                self.show_status("Reset to base directory")
            except Exception as fallback_ex:
                print(f"[ERROR] Emergency fallback failed: {fallback_ex}")

    def navigate_to_path(self, e=None):
        """Navigate to path entered in address bar"""
        try:
            path_str = self.address_bar.value.strip()
            if path_str:
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    self.current_path[0] = path
                    self.breadcrumb_path[0] = path  # Keep paths in sync
                    self.toggle_address_bar()  # Hide address bar
                    self.refresh()
                else:
                    self.show_status("Invalid path")
        except Exception as ex:
            self.show_status(f"Error: {ex}")

    def toggle_address_bar(self, e=None):
        """Toggle between breadcrumb and address bar"""
        self.address_bar.visible = not self.address_bar.visible
        self.breadcrumb.visible = not self.address_bar.visible
        
        if self.address_bar.visible:
            self.address_bar.value = str(self.current_path[0])
            self.address_bar.focus()
        
        try:
            self.address_bar.update()
            self.breadcrumb.update()
        except:
            pass

    def show_status(self, message: str):
        """Update status bar message"""
        self.status_text.value = message
        try:
            self.status_text.update()
        except:
            pass

    def toggle_view_mode(self, e=None):
        """Toggle between grid and list view"""
        self.view_mode = "list" if self.view_mode == "grid" else "grid"
        
        # Force visibility update immediately
        if self.view_mode == "grid":
            self.grid.visible = True
            self.list_view.visible = False
        else:
            self.grid.visible = False
            self.list_view.visible = True
            
        # Update the view button icon
        self.refresh()  # This will call update_view with proper visibility

    def sort_items(self, items: List[Path]) -> List[Path]:
        """Sort items based on current sort settings"""
        def get_sort_key(item: Path):
            try:
                if self.sort_by == "name":
                    return item.name.lower()
                elif self.sort_by == "size":
                    return item.stat().st_size if item.is_file() else 0
                elif self.sort_by == "date":
                    return item.stat().st_mtime
                elif self.sort_by == "type":
                    if item.is_dir():
                        return "0_folder"  # Folders first
                    return item.suffix.lower()
                else:
                    return item.name.lower()
            except:
                return ""

        # Separate directories and files
        dirs = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]
        # Sort each group
        dirs.sort(key=get_sort_key, reverse=not self.sort_ascending)
        files.sort(key=get_sort_key, reverse=not self.sort_ascending)
        # Return directories first, then files (traditional Explorer behavior)
        return dirs + files

    def change_sort(self, sort_by: str):
        """Change sort method"""
        if self.sort_by == sort_by:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_by = sort_by
            self.sort_ascending = True
        self.refresh()

    def build_grid_tile(self, item: Path):
        """Build grid view tile - BIGGER VERSION"""
        icon, color = get_icon_and_color(item)
        display_name = item.name
        short_name = display_name if len(display_name) <= 18 else display_name[:15] + "..."  # Increased length
        is_selected = item in self.selected_items

        def on_click_tile(e):
            self.handle_item_click(item, e)

        def on_right_click(e):
            self.show_context_menu(item, e)

        container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(getattr(ft.Icons, icon), size=72, color=color),  # Increased from 64 to 72
                    ft.Text(
                        short_name, 
                        size=13,  # Increased from 12 to 13
                        text_align="center", 
                        no_wrap=True,
                        weight=ft.FontWeight.W_500
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10  # Increased from 8 to 10
            ),
            tooltip=item.name,
            on_click=on_click_tile,
            on_long_press=on_right_click,
            padding=12,  # Increased from 10 to 12
            border_radius=12,  # Increased from 10 to 12
            data=item,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLUE) if is_selected else "transparent",
            border=ft.border.all(2 if is_selected else 1, 
                                ft.Colors.BLUE if is_selected else ft.Colors.TRANSPARENT)
        )

        def on_hover(e):
            if item not in self.selected_items:
                if e.data == "true":
                    container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
                else:
                    container.bgcolor = "transparent"
                    container.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                
                try:
                    container.update()
                except:
                    pass

        container.on_hover = on_hover
        return container

    def build_list_row(self, item: Path):
        """Build list view row - BIGGER VERSION"""
        icon, color = get_icon_and_color(item)
        is_selected = item in self.selected_items
        
        try:
            stat = item.stat()
            size = self.format_file_size(stat.st_size) if item.is_file() else ""
            modified = time.strftime("%m/%d/%Y %I:%M %p", time.localtime(stat.st_mtime))
        except:
            size = ""
            modified = ""

        def on_click_row(e):
            self.handle_item_click(item, e)

        def on_right_click(e):
            self.show_context_menu(item, e)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(getattr(ft.Icons, icon), size=28, color=color),  # Increased from 20 to 28
                    ft.Container(
                        content=ft.Text(
                            item.name, 
                            size=15,  # Increased from 13 to 15
                            weight=ft.FontWeight.W_500
                        ),
                        expand=True,
                        padding=ft.padding.only(left=12)  # Increased from 8 to 12
                    ),
                    ft.Container(
                        content=ft.Text(
                            size, 
                            size=14,  # Increased from 12 to 14
                            color=ft.Colors.GREY_700
                        ),
                        width=90  # Increased from 80 to 90
                    ),
                    ft.Container(
                        content=ft.Text(
                            modified, 
                            size=14,  # Increased from 12 to 14
                            color=ft.Colors.GREY_700
                        ),
                        width=140  # Increased from 130 to 140
                    ),
                ],
                spacing=12,  # Increased from 8 to 12
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),  # Increased padding
            on_click=on_click_row,
            on_long_press=on_right_click,
            data=item,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.BLUE) if is_selected else "transparent",
            border_radius=6,  # Increased from 4 to 6
            height=48,  # Added explicit height for bigger rows
        )

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        return f"{size:.1f} {size_names[i]}"

    def handle_item_click(self, item: Path, e=None):
        """Handle item selection and double-click"""
        now = time.time()
        
        # Check for double-click
        if (len(self.selected_items) == 1 and 
            item in self.selected_items and 
            (now - self.last_click_time["time"]) < 0.5):
            
            # Double-click action
            if item.is_dir():
                self.navigate_to_directory(item)
            else:
                self.open_file(item)
        else:
            # Single click - handle selection
            ctrl_pressed = e and hasattr(e, 'ctrl_key') and e.ctrl_key
            shift_pressed = e and hasattr(e, 'shift_key') and e.shift_key
            
            if ctrl_pressed:
                # Toggle selection
                if item in self.selected_items:
                    self.selected_items.remove(item)
                else:
                    self.selected_items.add(item)
            elif shift_pressed and self.selected_items:
                # Range selection (simplified - select all between first selected and this item)
                # This would need more complex logic for proper range selection
                self.selected_items.add(item)
            else:
                # Normal selection - clear others and select this
                self.selected_items.clear()
                self.selected_items.add(item)
            
            self.last_click_time["time"] = now
            self.highlight_selected()
            
            if len(self.selected_items) == 1:
                self.show_details(item)
            else:
                self.show_multiple_selection_details()

    def navigate_to_directory(self, directory: Path):
        """Navigate to a directory - WITH IMMEDIATE UI UPDATE"""
        try:
            print(f"[INFO] Navigating to directory: {directory}")
            self.clear_search_field()
            self.current_path[0] = directory
            self.breadcrumb_path[0] = directory  # Keep paths in sync
            self.selected_items.clear()
            
            # IMMEDIATELY update back button state
            self.update_back_button_state()
            
            self.refresh()
        except Exception as ex:
            self.show_status(f"Cannot access directory: {ex}")

    def open_file(self, file_path: Path):
        """Open a file with default application"""
        def confirm_open():
            try:
                os.startfile(file_path)
                self.show_status(f"Opened {file_path.name}")
            except Exception as ex:
                self.show_status(f"Could not open file: {ex}")
        show_confirm_dialog(self.page, "Open File", f"Open '{file_path.name}'?", confirm_open)

    def show_context_menu(self, item: Path, e=None):
        """Show context menu for item"""
        menu_items = []
        
        # Open
        if item.is_file():
            menu_items.append(
                ft.MenuItemButton(
                    content=ft.Text("Open"),
                    leading=ft.Icon(ft.Icons.OPEN_IN_NEW),
                    on_click=lambda _: self.open_file(item)
                )
            )
        
        # Cut, Copy, Delete
        menu_items.extend([
            ft.MenuItemButton(
                content=ft.Text("Cut"),
                leading=ft.Icon(ft.Icons.CONTENT_CUT),
                on_click=lambda _: self.cut_items()
            ),
            ft.MenuItemButton(
                content=ft.Text("Copy"),
                leading=ft.Icon(ft.Icons.CONTENT_COPY),
                on_click=lambda _: self.copy_items()
            ),
            ft.MenuItemButton(
                content=ft.Text("Delete"),
                leading=ft.Icon(ft.Icons.DELETE),
                on_click=lambda _: self.delete_items()
            ),
        ])
        
        # Rename (only for single selection)
        if len(self.selected_items) == 1:
            menu_items.append(
                ft.MenuItemButton(
                    content=ft.Text("Rename"),
                    leading=ft.Icon(ft.Icons.EDIT),
                    on_click=lambda _: self.rename_item(item)
                )
            )
        
        # Properties
        menu_items.append(
            ft.MenuItemButton(
                content=ft.Text("Properties"),
                leading=ft.Icon(ft.Icons.INFO),
                on_click=lambda _: self.show_properties(item)
            )
        )
        # Note: Flet doesn't have native context menus, so this would need 
        # to be implemented as a popup or overlay

    def cut_items(self):
        """Cut selected items to clipboard"""
        if self.selected_items:
            self.clipboard_items = list(self.selected_items)
            self.clipboard_operation = "cut"
            self.show_status(f"Cut {len(self.clipboard_items)} items")

    def copy_items(self):
        """Copy selected items to clipboard"""
        if self.selected_items:
            self.clipboard_items = list(self.selected_items)
            self.clipboard_operation = "copy"
            self.show_status(f"Copied {len(self.clipboard_items)} items")

    def paste_items(self):
        """Paste items from clipboard"""
        if not self.clipboard_items:
            return
            
        try:
            for item in self.clipboard_items:
                dest_path = self.current_path[0] / item.name
                
                if self.clipboard_operation == "copy":
                    if item.is_dir():
                        shutil.copytree(item, dest_path)
                    else:
                        shutil.copy2(item, dest_path)
                elif self.clipboard_operation == "cut":
                    shutil.move(str(item), str(dest_path))
            
            if self.clipboard_operation == "cut":
                self.clipboard_items.clear()
                
            self.show_status("Items pasted successfully")
            self.refresh()
            
        except Exception as ex:
            self.show_status(f"Paste failed: {ex}")

    def delete_items(self):
        """Delete selected items"""
        if not self.selected_items:
            return
            
        def confirm_delete():
            try:
                for item in self.selected_items:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                        
                self.show_status(f"Deleted {len(self.selected_items)} items")
                self.selected_items.clear()
                self.refresh()
                
            except Exception as ex:
                self.show_status(f"Delete failed: {ex}")

        items_text = f"{len(self.selected_items)} item(s)"
        show_confirm_dialog(
            self.page, 
            "Delete Items", 
            f"Are you sure you want to delete {items_text}?", 
            confirm_delete
        )

    def rename_item(self, item: Path):
        """Rename an item (would need a dialog implementation)"""
        # This would need a rename dialog
        pass

    def show_properties(self, item: Path):
        """Show item properties (would need a properties dialog)"""
        # This would need a properties dialog
        pass

    def select_all(self):
        """Select all items in current view"""
        try:
            query = self.search_field.value.strip() if self.search_field.value else ""
            
            if query:
                items = search_all(query)
            else:
                items = list(self.current_path[0].iterdir())
                
            self.selected_items.update(items)
            self.highlight_selected()
            self.show_status(f"Selected {len(self.selected_items)} items")
            
        except Exception as ex:
            self.show_status(f"Select all failed: {ex}")

    def show_multiple_selection_details(self):
        """Show details for multiple selected items"""
        try:
            total_size = 0
            file_count = 0
            folder_count = 0
            
            for item in self.selected_items:
                if item.is_file():
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except:
                        pass
                else:
                    folder_count += 1
                    
            # Update details panel with summary
            # This would need to be implemented in the DetailsPane class
            
        except Exception as ex:
            print(f"[ERROR] Multiple selection details failed: {ex}")

    def highlight_selected(self):
        """Highlight selected items"""
        try:
            if self.view_mode == "grid":
                controls = self.grid.controls
            else:
                controls = self.list_view.controls
                
            for control in controls:
                if not hasattr(control, 'data'):
                    continue
                    
                item = control.data
                is_selected = item in self.selected_items
                
                if is_selected:
                    control.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.BLUE)
                    control.border = ft.border.all(2, ft.Colors.BLUE)
                else:
                    control.bgcolor = "transparent"
                    control.border = ft.border.all(1, ft.Colors.TRANSPARENT)
                
                try:
                    control.update()
                except:
                    pass
                    
        except Exception as ex:
            print(f"[ERROR] Highlight selection failed: {ex}")

    def on_search_change(self, e):
        """Handle search field changes"""
        try:
            has_text = bool(e.control.value and e.control.value.strip())
            self.clear_search_btn.visible = has_text
            
            if hasattr(self.clear_search_btn, 'page') and self.clear_search_btn.page:
                self.clear_search_btn.update()
                
        except Exception as ex:
            print(f"[ERROR] Search change handler failed: {ex}")

    def clear_search_field(self):
        """Clear the search field"""
        try:
            self.search_field.value = ""
            self.clear_search_btn.visible = False
            
            if hasattr(self.search_field, 'page') and self.search_field.page:
                self.search_field.update()
            if hasattr(self.clear_search_btn, 'page') and self.clear_search_btn.page:
                self.clear_search_btn.update()
        except Exception as ex:
            print(f"[ERROR] Clear search field failed: {ex}")

    def clear_search(self, e=None):
        """Clear search and return to current directory"""
        try:
            self.clear_search_field()
            self.breadcrumb_path[0] = self.current_path[0]  # Keep paths in sync
            self.refresh()
        except Exception as ex:
            print(f"[ERROR] Clear search failed: {ex}")

    def show_details(self, item: Path):
        try:
            self.details_panel.update_details(item)
        except Exception as ex:
            print(f"[ERROR] Show details failed: {ex}")

    def deselect_all(self):
        try:
            self.selected_items.clear()
            self.highlight_selected()
            self.details_panel.clean()
        except Exception as ex:
            print(f"[ERROR] Deselect all failed: {ex}")

    def update_breadcrumb(self):
        try:
            self.breadcrumb.controls.clear()
            # Use current_path for display - simplified
            parts = list(self.current_path[0].parts)
            
            for i, part in enumerate(parts):
                partial_path = Path(*parts[:i + 1])
                
                def create_breadcrumb_click(p):
                    def go_to_path(e):
                        try:
                            if p == BASE_DIR:
                                self.clear_search_field()
                                
                            # Navigate to clicked path
                            self.current_path[0] = p
                            self.breadcrumb_path[0] = p  # Keep paths in sync
                            self.refresh()
                        except Exception as ex:
                            print(f"[ERROR] Breadcrumb click failed: {ex}")
                    return go_to_path

                # Highlight current location
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
            
            try:
                if hasattr(self.breadcrumb, 'page') and self.breadcrumb.page:
                    self.breadcrumb.update()
            except:
                pass
        except Exception as ex:
            print(f"[ERROR] Breadcrumb update failed: {ex}")

    def update_view(self, items):
        """Update the current view (grid or list) with items"""
        try:
            sorted_items = self.sort_items(items)
            
            if self.view_mode == "grid":
                # Clear and populate grid view
                self.grid.controls.clear()
                
                for item in sorted_items:
                    tile = self.build_grid_tile(item)
                    if tile:
                        self.grid.controls.append(tile)
                
                # Show only grid container, hide list container
                if hasattr(self, 'grid_container') and hasattr(self, 'list_container'):
                    self.grid_container.visible = True
                    self.list_container.visible = False
                    
                    try:
                        self.grid_container.update()
                        self.list_container.update()
                    except:
                        pass
                        
                # Fallback visibility control
                self.grid.visible = True
                self.list_view.visible = False
                        
                # Safe update
                try:
                    if hasattr(self.grid, 'page') and self.grid.page:
                        self.grid.update()
                except:
                    pass
                    
            else:  # list view
                # Clear and populate list view
                self.list_view.controls.clear()
                
                # Add header row for list view - BIGGER VERSION
                header = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(width=28),  # Icon space - increased to match icon size
                            ft.TextButton(
                                "Name",
                                on_click=lambda _: self.change_sort("name"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.BLUE if self.sort_by == "name" else ft.Colors.BLACK
                                )
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Size",
                                on_click=lambda _: self.change_sort("size"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.BLUE if self.sort_by == "size" else ft.Colors.BLACK
                                ),
                                width=90  # Increased to match row width
                            ),
                            ft.TextButton(
                                "Date Modified",
                                on_click=lambda _: self.change_sort("date"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.BLUE if self.sort_by == "date" else ft.Colors.BLACK
                                ),
                                width=140  # Increased to match row width
                            ),
                        ],
                        spacing=12,  # Increased to match row spacing
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),  # Increased padding
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
                    height=50,  # Added explicit height for bigger header
                )
                self.list_view.controls.append(header)
                
                for item in sorted_items:
                    row = self.build_list_row(item)
                    if row:
                        self.list_view.controls.append(row)
                
                # Show only list container, hide grid container
                if hasattr(self, 'grid_container') and hasattr(self, 'list_container'):
                    self.grid_container.visible = False
                    self.list_container.visible = True
                    
                    try:
                        self.grid_container.update()
                        self.list_container.update()
                    except:
                        pass
                        
                # Fallback visibility control
                self.list_view.visible = True
                self.grid.visible = False
                        
                # Safe update
                try:
                    if hasattr(self.list_view, 'page') and self.list_view.page:
                        self.list_view.update()
                except:
                    pass
                    
            # Update status bar
            item_count = len(sorted_items)
            selected_count = len(self.selected_items)
            
            if selected_count > 0:
                self.show_status(f"{selected_count} of {item_count} items selected")
            else:
                self.show_status(f"{item_count} items")
                
        except Exception as ex:
            print(f"[ERROR] View update failed: {ex}")

    def refresh(self, e=None):
        """Refresh the current view - WITH BACK BUTTON UPDATE"""
        try:
            # Ensure current_path is valid before refreshing
            if not self.current_path or not self.current_path[0] or not self.current_path[0].exists():
                print("[WARNING] Invalid current_path, resetting to BASE_DIR")
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
                
            self.update_breadcrumb()
            
            query = self.search_field.value.strip() if self.search_field.value else ""
            
            if query:
                results = search_all(query)
            else:
                results = list(self.current_path[0].iterdir())
            
            self.update_view(results)
            
            # Update back button state after refresh
            self.update_back_button_state()
            
        except Exception as ex:
            print(f"[ERROR] Refresh failed: {ex}")
            self.show_status(f"Error: {ex}")
            
            # Fallback: reset to BASE_DIR if refresh fails
            try:
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
                self.update_breadcrumb()
                results = list(BASE_DIR.iterdir())
                self.update_view(results)
                self.update_back_button_state()
            except Exception as fallback_ex:
                print(f"[ERROR] Fallback refresh also failed: {fallback_ex}")

    def force_ui_refresh(self):
        """Force complete UI refresh - call this when switching TO this panel"""
        try:
            print("[INFO] Forcing complete UI refresh...")
            
            # Ensure we have a valid current path
            if not self.current_path or not self.current_path[0] or not self.current_path[0].exists():
                print("[WARNING] Invalid current path, resetting to BASE_DIR")
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
            
            # Update back button state
            self.update_back_button_state()
            
            # Refresh breadcrumb
            self.update_breadcrumb()
            
            # Refresh file view
            query = self.search_field.value.strip() if self.search_field.value else ""
            if query:
                results = search_all(query)
            else:
                results = list(self.current_path[0].iterdir())
            
            self.update_view(results)
            
            # Force update of toolbar container if it exists
            if self.toolbar_container:
                try:
                    self.toolbar_container.update()
                except:
                    pass
                    
            # Force update of main layout if it exists
            if self.main_layout:
                try:
                    self.main_layout.update()
                except:
                    pass
            
            # Force page update
            if hasattr(self, 'page') and self.page:
                try:
                    self.page.update()
                except:
                    pass
                    
            self.show_status(f"Refreshed view at {self.current_path[0]}")
            print(f"[INFO] UI refresh completed at {self.current_path[0]}")
            
        except Exception as ex:
            print(f"[ERROR] Force UI refresh failed: {ex}")
            
    def update_back_button_state(self):
        """Update just the back button state"""
        if not self.back_button:
            return
            
        try:
            can_go_back = False
            current = self.current_path[0]
            if current and current.exists():
                parent = current.parent
                can_go_back = (parent != current and 
                              parent.exists() and 
                              os.access(parent, os.R_OK))
                              
            # Update button properties
            self.back_button.disabled = not can_go_back
            self.back_button.icon_color = ft.Colors.GREY_700 if can_go_back else ft.Colors.GREY_400
            self.back_button.tooltip = "Back" + ("" if can_go_back else " (Cannot go back)")
            
            # Force button update
            try:
                self.back_button.update()
            except:
                pass
                
            print(f"[INFO] Back button state updated: can_go_back={can_go_back}")
            
        except Exception as ex:
            print(f"[ERROR] Back button state update failed: {ex}")

    def on_panel_activated(self):
        """Called when this panel becomes active - COMPLETE REFRESH"""
        print("[INFO] Browser panel activated")
        self.force_ui_refresh()

    def update_toolbar_buttons(self):
        """Update toolbar button states after navigation - NOW ACTUALLY WORKS"""
        try:
            # Force recreation of toolbar to update button states
            # This ensures back button state is recalculated
            if hasattr(self, 'page') and self.page:
                # Trigger a refresh that will recreate the toolbar
                self.refresh()
        except Exception as ex:
            print(f"[ERROR] Toolbar update failed: {ex}")

    def create_toolbar(self):
        """Create the main toolbar with navigation and controls - WITH STORED REFERENCES"""
        
        # Create back button and store reference for dynamic updates
        can_go_back = self.get_back_button_state()
        
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Back" + ("" if can_go_back else " (Cannot go back)"),
            on_click=self.go_back,
            disabled=not can_go_back,
            icon_color=ft.Colors.GREY_700 if can_go_back else ft.Colors.GREY_400,
            icon_size=20,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(8),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                }
            )
        )
        
        refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh",
            on_click=self.refresh,
            icon_color=ft.Colors.GREY_700,
            icon_size=20,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(8),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                }
            )
        )
        
        # View toggle button
        view_icon = ft.Icons.VIEW_LIST if self.view_mode == "grid" else ft.Icons.GRID_VIEW
        view_btn = ft.IconButton(
            icon=view_icon,
            tooltip=f"Switch to {'List' if self.view_mode == 'grid' else 'Grid'} View",
            on_click=self.toggle_view_mode,
            icon_color=ft.Colors.GREY_700,
            icon_size=20,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(8),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.GREY)
                }
            )
        )

        # Create and store toolbar container reference
        self.toolbar_container = ft.Container(
            content=ft.Column([
                # Main toolbar row
                ft.Row(
                    [
                        # Left side - Navigation controls
                        ft.Row(
                            [
                                self.back_button,  # Using stored reference
                                ft.Container(
                                    width=1,
                                    height=24,
                                    bgcolor=ft.Colors.GREY_300,
                                    margin=ft.margin.symmetric(horizontal=8)
                                ),
                                refresh_btn,
                                view_btn,
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        
                        # Right side - Search
                        self.search_field,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                
                # Address bar / Breadcrumb row
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    self.breadcrumb,
                                    self.address_bar,
                                ],
                                spacing=0,
                            ),
                            expand=True,
                            on_click=self.toggle_address_bar,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY),
                        ),
                    ],
                ),
            ], spacing=8),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.GREY),
        )
        
        return self.toolbar_container

    def get_back_button_state(self):
        """Get current back button state"""
        can_go_back = False
        try:
            current = self.current_path[0]
            if not current or not current.exists():
                return False
            parent = current.parent
            can_go_back = (parent != current and 
                          parent.exists() and 
                          os.access(parent, os.R_OK))
        except (OSError, ValueError, AttributeError):
            can_go_back = False
        return can_go_back

    def create_status_bar(self):
        """Create status bar at bottom"""
        return ft.Container(
            content=ft.Row(
                [
                    self.status_text,
                    ft.Container(expand=True),
                    ft.Text(
                        f"View: {self.view_mode.title()}",
                        size=12,
                        color=ft.Colors.GREY_700
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.GREY),
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

    def create_content(self):
        """Create the main content area - WITH STORED REFERENCES FOR PANEL SWITCHING"""
        
        # Initialize views with proper visibility
        self.list_view.visible = False  # Start with grid view
        self.grid.visible = True
        
        # Create separate containers for each view to prevent overlap
        grid_container = ft.Container(
            content=self.grid,
            expand=True,
            visible=True
        )
        
        list_container = ft.Container(
            content=self.list_view,
            expand=True,
            visible=False
        )
        
        # Use Column instead of Stack to prevent overlaying
        view_container = ft.Container(
            content=ft.Column(
                [
                    grid_container,
                    list_container,
                ],
                expand=True,
                spacing=0
            ),
            expand=True,
        )
        
        # Create and store main layout reference
        self.main_layout = ft.Column([
            # Toolbar - will be recreated each time with proper button states
            self.create_toolbar(),
            
            # Main content area
            ft.Container(
                content=ft.Row([
                    # Main view area
                    ft.Container(
                        expand=True,
                        content=ft.GestureDetector(
                            on_tap=lambda e: self.deselect_all(),
                            content=view_container
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
            
            # Status bar
            self.create_status_bar(),
        ], 
        expand=True,
        spacing=0
        )

        # Store references to containers for visibility control
        self.grid_container = grid_container
        self.list_container = list_container

        # Initialize the view with proper error handling
        self.initialize_view()
        
        return self.main_layout

    def initialize_view(self):
        """Initialize or reset the view - safe for panel switching"""
        try:
            # Ensure we have a valid current path
            if not self.current_path or not self.current_path[0]:
                self.current_path = [BASE_DIR]
            
            # Validate the current path exists
            if not self.current_path[0].exists():
                print(f"[WARNING] Current path {self.current_path[0]} no longer exists, resetting to BASE_DIR")
                self.current_path = [BASE_DIR]
            
            # Keep both paths in sync
            self.breadcrumb_path[0] = self.current_path[0]
            
            # Update UI components
            self.update_breadcrumb()
            
            # Load directory contents
            results = list(self.current_path[0].iterdir())
            self.update_view(results)
            
            print(f"[INFO] View initialized at: {self.current_path[0]}")
            
        except Exception as ex:
            print(f"[ERROR] View initialization failed: {ex}")
            # Ultimate fallback
            try:
                self.current_path = [BASE_DIR]
                self.breadcrumb_path = [BASE_DIR]
                self.update_breadcrumb()
                results = list(BASE_DIR.iterdir())
                self.update_view(results)
                print(f"[INFO] Fallback initialization successful")
            except Exception as fallback_ex:
                print(f"[ERROR] Even fallback initialization failed: {fallback_ex}")

    def handle_key_press(self, e):
        """Handle keyboard shortcuts"""
        try:
            if e.key == "F5":
                self.refresh()
            elif e.key == "Delete" and self.selected_items:
                self.delete_items()
            elif e.key == "F2" and len(self.selected_items) == 1:
                self.rename_item(list(self.selected_items)[0])
            elif e.ctrl and e.key == "a":
                self.select_all()
            elif e.ctrl and e.key == "c":
                self.copy_items()
            elif e.ctrl and e.key == "x":
                self.cut_items()
            elif e.ctrl and e.key == "v":
                self.paste_items()
            elif e.key == "Backspace":
                self.go_back()  # NOW USES WORKING go_back METHOD
            elif e.key == "Enter" and len(self.selected_items) == 1:
                item = list(self.selected_items)[0]
                if item.is_dir():
                    self.navigate_to_directory(item)
                else:
                    self.open_file(item)
                    
        except Exception as ex:
            print(f"[ERROR] Key press handler failed: {ex}")

# Additional helper functions for enhanced functionality
def get_file_type_description(item: Path) -> str:
    """Get user-friendly file type description"""
    if item.is_dir():
        return "File folder"
    
    ext = item.suffix.lower()
    type_map = {
        '.txt': 'Text Document',
        '.pdf': 'PDF Document',
        '.doc': 'Microsoft Word Document',
        '.docx': 'Microsoft Word Document',
        '.xls': 'Microsoft Excel Worksheet',
        '.xlsx': 'Microsoft Excel Worksheet',
        '.ppt': 'Microsoft PowerPoint Presentation',
        '.pptx': 'Microsoft PowerPoint Presentation',
        '.zip': 'Compressed (zipped) Folder',
        '.jpg': 'JPEG Image',
        '.jpeg': 'JPEG Image',
        '.png': 'PNG Image',
        '.gif': 'GIF Image',
        '.mp3': 'MP3 Audio File',
        '.mp4': 'MP4 Video File',
        '.exe': 'Application',
        '.py': 'Python File',
        '.js': 'JavaScript File',
        '.html': 'HTML Document',
        '.css': 'CSS Stylesheet',
    }
    
    return type_map.get(ext, f'{ext.upper()[1:]} File' if ext else 'File')
