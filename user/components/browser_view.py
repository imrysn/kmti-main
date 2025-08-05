import flet as ft
import os
import time
import threading
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict
from utils.config_loader import get_base_dir
from utils.dialog import show_confirm_dialog
from admin.details_pane import DetailsPane

BASE_DIR = get_base_dir()
INDEX_CACHE_PATH = Path("cache/index.json")

# ===== GLOBAL CACHED SEARCH ENGINE FOR BROWSER =====
class BrowserGlobalSearch:
    def __init__(self):
        self.file_index: List[Dict] = []
        self.search_cache: Dict[str, List[Path]] = {}
        self.index_lock = threading.RLock()
        self.cache_lock = threading.RLock()
        self.is_loaded = False
        
    def load_cached_index(self):
        """Load existing cached index with validation"""
        try:
            if INDEX_CACHE_PATH.exists():
                print(f"[DEBUG] Browser loading cached index from {INDEX_CACHE_PATH}")
                with open(INDEX_CACHE_PATH, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Validate the cached data structure
                if not isinstance(cached_data, list):
                    print("[WARNING] Browser: Invalid cache format: not a list")
                    return False
                
                # Convert old string format to new dict format if needed
                converted_data = []
                for item in cached_data:
                    if isinstance(item, str):
                        # Convert string path to dict format
                        path_obj = Path(item)
                        if path_obj.exists():
                            try:
                                stat = path_obj.stat()
                                converted_data.append({
                                    'path': str(path_obj),
                                    'name': path_obj.name,
                                    'type': 'directory' if path_obj.is_dir() else 'file',
                                    'size': 0 if path_obj.is_dir() else stat.st_size,
                                    'modified': stat.st_mtime,
                                    'extension': '' if path_obj.is_dir() else path_obj.suffix.lower(),
                                    'keywords': self._generate_keywords(path_obj.name)
                                })
                            except Exception as e:
                                print(f"[DEBUG] Browser failed to convert {item}: {e}")
                                continue
                    elif isinstance(item, dict):
                        # Already in correct format
                        converted_data.append(item)
                    else:
                        print(f"[WARNING] Browser unknown item type: {type(item)}")
                        continue
                
                if converted_data:
                    with self.index_lock:
                        self.file_index = converted_data
                        self.is_loaded = True
                    
                    print(f"[DEBUG] Browser loaded and converted {len(converted_data)} items from cached index")
                    return True
                else:
                    print("[WARNING] Browser: No valid items after conversion")
                    return False
                    
        except Exception as e:
            print(f"[WARNING] Browser failed to load cached index: {e}")
        
        return False
    
    def _generate_keywords(self, filename: str) -> List[str]:
        """Generate search keywords from filename"""
        keywords = []
        
        # Split by common separators
        separators = [' ', '_', '-', '.', '(', ')', '[', ']']
        words = [filename.lower()]
        
        for sep in separators:
            new_words = []
            for word in words:
                new_words.extend(word.split(sep))
            words = [w.strip() for w in new_words if w.strip()]
        
        keywords.extend(words)
        return list(set(keywords))
    
    def search(self, query: str, max_results: int = 200) -> List[Path]:
        """Global search using cached index with validation"""
        if not query or not self.is_loaded:
            print(f"[DEBUG] Browser search skipped - query: '{query}', loaded: {self.is_loaded}")
            return []
        
        # Check cache
        cache_key = f"{query}_{max_results}"
        with self.cache_lock:
            if cache_key in self.search_cache:
                print(f"[DEBUG] Browser returning cached results for '{query}'")
                return self.search_cache[cache_key]
        
        query_lower = query.lower()
        scored_results = []
        processed = 0
        errors = 0
        
        print(f"[DEBUG] Browser global search for '{query}' in {len(self.file_index)} indexed items")
        
        with self.index_lock:
            for item in self.file_index:
                processed += 1
                try:
                    # Validate item structure first
                    if not isinstance(item, dict):
                        errors += 1
                        if errors <= 5:  # Limit error spam
                            print(f"[DEBUG] Browser item {processed} is not dict: {type(item)}")
                        continue
                    
                    if 'path' not in item or 'name' not in item:
                        errors += 1
                        if errors <= 5:
                            print(f"[DEBUG] Browser item {processed} missing required fields")
                        continue
                    
                    score = self._calculate_search_score(item, query_lower)
                    
                    if score > 0:
                        path_obj = Path(str(item['path']))
                        if path_obj.exists():  # Verify path still exists
                            scored_results.append((score, path_obj))
                        
                        if len(scored_results) >= max_results * 2:
                            break
                            
                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Limit error spam
                        print(f"[DEBUG] Browser search error for item {processed}: {e}")
                    continue
        
        # Sort by score and extract paths
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [path for score, path in scored_results[:max_results]]
        
        print(f"[DEBUG] Browser search processed {processed} items, {errors} errors, found {len(results)} results for '{query}'")
        
        # Cache results
        with self.cache_lock:
            self.search_cache[cache_key] = results
            
        return results
    
    def _calculate_search_score(self, item: Dict, query: str) -> int:
        """Calculate search relevance score with validation"""
        score = 0
        
        if not query:
            return 0
        
        try:
            # Validate item structure
            if not isinstance(item, dict):
                return 0
            
            if 'name' not in item:
                return 0
            
            name_lower = str(item['name']).lower()
            
            # Exact name match (highest score)
            if query == name_lower:
                score += 100
            
            # Name starts with query
            elif name_lower.startswith(query):
                score += 90
            
            # Name contains query
            elif query in name_lower:
                score += 70
            
            # Keyword matches
            keywords = item.get('keywords', [])
            if isinstance(keywords, list):
                for keyword in keywords:
                    if isinstance(keyword, str) and query in keyword:
                        score += 30
                        break
            
            # Extension match
            extension = item.get('extension', '')
            if isinstance(extension, str) and query == extension.lstrip('.'):
                score += 60
            
            return score
            
        except Exception as e:
            return 0

# Global search engine instance for browser
browser_global_search = BrowserGlobalSearch()

class BrowserView:
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
        self.navigation = None
        
        # State management
        self.current_path = [BASE_DIR]
        self.selected_item = {"path": None}
        self.last_click_time = {"time": 0}
        self.current_search_thread = None
        self.search_stop_event = threading.Event()
        
        # UI Components
        self.details_panel = DetailsPane()
        self.breadcrumb = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.START)
        
        # ===== OPTIMIZED GRID =====
        self.grid = ft.GridView(
            expand=True,
            runs_count=8,  # More columns for better use of space
            max_extent=120,  # Smaller tiles for more content
            child_aspect_ratio=0.85,
            spacing=8,
            run_spacing=8,
        )
        
        # ===== SIMPLE SEARCH UI - ENTER KEY ONLY =====
        self.search_field = ft.TextField(
            hint_text="Search files and folders... (Press Enter)",
            width=350,
            height=40,
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            prefix_icon=ft.icons.SEARCH,
            on_submit=self.on_search_submit
            # Removed on_change to only trigger on Enter
        )
        
        # Search state
        self.search_active = False
        
        # ===== LOADING AND STATUS =====
        self.loading_indicator = ft.ProgressBar(
            width=300,
            height=4,
            visible=False,
            color=ft.Colors.BLUE
        )
        
        self.status_text = ft.Text(
            "Ready",
            size=12,
            color=ft.Colors.GREY_600
        )
        
        # Initialize search engine
        self._initialize_search_engine()
    
    def set_navigation(self, navigation):
        self.navigation = navigation
    
    def _initialize_search_engine(self):
        """Initialize global cached search engine"""
        browser_global_search.load_cached_index()
        self.status_text.value = f"Ready - Global search loaded"
        if self.status_text.page:
            self.status_text.update()
    
    def show_loading(self, show: bool):
        """Show/hide loading indicator"""
        self.loading_indicator.visible = show
        if self.loading_indicator.page:
            self.loading_indicator.update()
    
    def on_search_submit(self, e):
        """Handle search submission - ENTER KEY ONLY"""
        query = e.control.value.strip()
        if query:
            self.perform_global_search(query)
        else:
            self.clear_search()
    
    def perform_global_search(self, query: str):
        """Perform global search using cached index"""
        if not query:
            return
        
        print(f"[DEBUG] Browser starting global search for: '{query}'")
        self.search_active = True
        
        self.show_loading(True)
        self.status_text.value = f"Searching globally for '{query}'..."
        
        def search_worker():
            try:
                # Wait for global search to be ready
                max_wait = 10  # seconds
                waited = 0
                while (not browser_global_search.is_loaded) and waited < max_wait:
                    time.sleep(0.5)
                    waited += 0.5
                
                if not browser_global_search.is_loaded:
                    self.status_text.value = "Search index not ready"
                    self.show_loading(False)
                    if self.status_text.page:
                        self.status_text.update()
                    return
                
                results = browser_global_search.search(query, max_results=200)
                print(f"[DEBUG] Browser global search completed: {len(results)} results")
                
                # Update UI on main thread
                def update_ui():
                    self.update_grid(results)
                    self.update_breadcrumb()
                    self.show_loading(False)
                    self.status_text.value = f"Global search: found {len(results)} results for '{query}'"
                    if self.status_text.page:
                        self.status_text.update()
                
                # Schedule UI update
                self.page.add(ft.Container())  # Trigger update
                update_ui()
                
            except Exception as e:
                print(f"[ERROR] Browser global search failed: {e}")
                self.show_loading(False)
                self.status_text.value = "Search failed"
                if self.status_text.page:
                    self.status_text.update()
        
        threading.Thread(target=search_worker, daemon=True).start()
    
    def clear_search(self):
        """Clear search and show current directory"""
        self.search_active = False
        self.refresh_directory()
    
    def get_icon_and_color(self, item: Path):
        """Get appropriate icon and color for file/folder"""
        if item.is_dir():
            return ft.icons.FOLDER, "#FF9100"
        
        ext = item.suffix.lower()
        
        # Document icons
        if ext == ".pdf":
            return ft.icons.PICTURE_AS_PDF, "#FF0000"
        elif ext in [".doc", ".docx"]:
            return ft.icons.DESCRIPTION, "#1976D2"
        elif ext in [".xls", ".xlsx"]:
            return ft.icons.TABLE_CHART, "#0F9D58"
        elif ext in [".ppt", ".pptx"]:
            return ft.icons.SLIDESHOW, "#FF6F00"
        
        # Media icons
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            return ft.icons.IMAGE, "#4CAF50"
        elif ext in [".mp4", ".avi", ".mkv", ".mov"]:
            return ft.icons.VIDEOCAM, "#9C27B0"
        elif ext in [".mp3", ".wav", ".flac"]:
            return ft.icons.AUDIOTRACK, "#FF5722"
        
        # Archive icons
        elif ext in [".zip", ".rar", ".7z"]:
            return ft.icons.FOLDER_ZIP, "#FF9800"
        
        # Code icons
        elif ext in [".py", ".js", ".html", ".css", ".java"]:
            return ft.icons.CODE, "#607D8B"
        
        # Default
        else:
            return ft.icons.DESCRIPTION, "#757575"
    
    def build_tile(self, item: Path):
        """Build optimized file/folder tile"""
        icon, color = self.get_icon_and_color(item)
        display_name = item.name
        short_name = display_name if len(display_name) <= 12 else display_name[:9] + "..."
        
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
                    self.search_field.value = ""  # Clear search when navigating
                    self.search_active = False
                    self.refresh_directory()
                    if self.search_field.page:
                        self.search_field.update()
                else:
                    def confirm_open():
                        try:
                            os.startfile(item)
                        except Exception as ex:
                            print(f"[ERROR] Could not open file: {ex}")
                    
                    show_confirm_dialog(self.page, "Open File", f"Open '{item.name}'?", confirm_open)
        
        # Enhanced tile with better styling
        container = ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=48, color=color),
                ft.Text(
                    short_name,
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
            tooltip=f"{item.name}\n{self._get_file_info(item)}",
            on_click=on_click_tile,
            padding=8,
            border_radius=8,
            data=item,
            bgcolor="transparent",
            border=ft.border.all(0.5, ft.Colors.TRANSPARENT)
        )
        
        def on_hover(e):
            if self.selected_item["path"] != item:
                if e.data == "true":
                    container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
                    container.border = ft.border.all(1, ft.Colors.BLUE_300)
                else:
                    container.bgcolor = "transparent"
                    container.border = ft.border.all(0.5, ft.Colors.TRANSPARENT)
                container.update()
        
        container.on_hover = on_hover
        return container
    
    def _get_file_info(self, item: Path) -> str:
        """Get file information for tooltip"""
        try:
            if item.is_dir():
                # Count items in directory
                try:
                    count = len(list(item.iterdir()))
                    return f"Folder • {count} items"
                except:
                    return "Folder"
            else:
                # File size
                size_bytes = item.stat().st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                
                return f"File • {size_str}"
        except:
            return "Unknown"
    
    def highlight_selected(self):
        """Highlight selected item"""
        for tile in self.grid.controls:
            path = tile.data
            if path == self.selected_item["path"]:
                tile.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.BLUE)
                tile.border = ft.border.all(2, ft.Colors.BLUE)
            else:
                tile.bgcolor = "transparent"
                tile.border = ft.border.all(0.5, ft.Colors.TRANSPARENT)
            tile.update()
    
    def show_details(self, item: Path):
        """Show item details"""
        self.details_panel.update_details(item)
    
    def deselect_all(self):
        """Deselect all items"""
        self.selected_item["path"] = None
        for tile in self.grid.controls:
            tile.bgcolor = "transparent"
            tile.border = ft.border.all(0.5, ft.Colors.TRANSPARENT)
            tile.update()
        self.details_panel.clean()
    
    def go_back(self, e=None):
        """Navigate back"""
        if self.search_active:
            # Exit search mode
            self.search_field.value = ""
            self.search_active = False
            self.refresh_directory()
            if self.search_field.page:
                self.search_field.update()
        elif self.current_path[0] != BASE_DIR:
            # Navigate back in directory
            self.current_path[0] = self.current_path[0].parent
            self.search_field.value = ""
            self.search_active = False
            self.refresh_directory()
            if self.search_field.page:
                self.search_field.update()
    
    def update_breadcrumb(self):
        """Update breadcrumb navigation"""
        if self.breadcrumb.page is None:
            return
            
        self.breadcrumb.controls.clear()
        
        if self.search_active:
            # Show search breadcrumb
            self.breadcrumb.controls.append(
                ft.Text("Search Results", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
            )
        else:
            # Show normal path breadcrumb
            parts = list(self.current_path[0].parts)
            
            for i, part in enumerate(parts):
                partial_path = Path(*parts[:i + 1])
                
                def go_to_path(_, p=partial_path):
                    self.current_path[0] = p
                    self.search_field.value = ""
                    self.search_active = False
                    self.refresh_directory()
                    if self.search_field.page:
                        self.search_field.update()
                
                self.breadcrumb.controls.append(
                    ft.TextButton(
                        text=part,
                        on_click=go_to_path,
                        style=ft.ButtonStyle(
                            color={ft.ControlState.DEFAULT: ft.Colors.BLUE_800}
                        )
                    )
                )
                if i < len(parts) - 1:
                    self.breadcrumb.controls.append(
                        ft.Text("›", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
                    )
        
        self.breadcrumb.update()
    
    def update_grid(self, items):
        """Update grid with items"""
        self.grid.controls.clear()
        
        for item in items[:100]:  # Limit for performance
            try:
                if item.exists():  # Check if path still exists
                    self.grid.controls.append(self.build_tile(item))
            except Exception as e:
                print(f"[WARNING] Skipping invalid item: {e}")
                continue
        
        if self.grid.page:
            self.grid.update()
    
    def refresh_directory(self):
        """Refresh current directory view"""
        self.show_loading(True)
        self.update_breadcrumb()
        
        def load_directory():
            try:
                items = sorted(self.current_path[0].iterdir())
                self.update_grid(items)
                self.status_text.value = f"{len(items)} items"
            except Exception as ex:
                print(f"[ERROR] Cannot read directory: {ex}")
                self.status_text.value = "Error reading directory"
            finally:
                self.show_loading(False)
                if self.status_text.page:
                    self.status_text.update()
        
        threading.Thread(target=load_directory, daemon=True).start()
    
    def create_toolbar(self):
        """Create simple toolbar without filters"""
        return ft.Column([
            # Main toolbar
            ft.Row([
                ft.IconButton(
                    ft.icons.ARROW_BACK,
                    tooltip="Back (Alt+Left)",
                    on_click=self.go_back,
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.HOVERED: ft.Colors.GREY_200}
                    )
                ),
                ft.IconButton(
                    ft.icons.REFRESH,
                    tooltip="Refresh (F5)",
                    on_click=lambda e: self.refresh_directory(),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.HOVERED: ft.Colors.GREY_200}
                    )
                ),
                
                # Spacer
                ft.Container(width=20),
                
                # Breadcrumb
                self.breadcrumb,
                
                # Right spacer
                ft.Container(expand=True),
                
                # Search field
                self.search_field,
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            # Status row
            ft.Row([
                self.status_text,
                ft.Container(expand=True),
                self.loading_indicator,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=10)
    
    def create_content(self):
        """Create main content layout"""
        layout = ft.Column([
            ft.Container(content=self.create_toolbar(), padding=10),
            ft.Divider(height=1),
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
                    height=500,
                    alignment=ft.alignment.top_left,
                    margin=10,
                )
            ], expand=True),
        ], expand=True, spacing=0)
        
        # Initial load
        threading.Timer(0.1, self.refresh_directory).start()
        return layout