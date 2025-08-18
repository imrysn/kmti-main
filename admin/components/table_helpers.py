import flet as ft
from datetime import datetime
from typing import List, Dict, Callable, Optional


class TableHelper:
    
    def __init__(self, config, enhanced_logger):

        self.config = config
        self.enhanced_logger = enhanced_logger
        self.column_configs = {
            "xs": {"file": True, "user": False, "team": False, "size": False, "submitted": False, "status": True},
            "sm": {"file": True, "user": True, "team": False, "size": False, "submitted": False, "status": True},
            "md": {"file": True, "user": True, "team": True, "size": False, "submitted": True, "status": True},
            "lg": {"file": True, "user": True, "team": True, "size": True, "submitted": True, "status": True}
        }
    
    def create_responsive_table(self, on_file_select: Callable) -> ft.DataTable:
        """Create responsive table that adapts to parent container."""
        try:
            min_height = self.config.get_ui_constant('table_row_min_height', 40)
            max_height = self.config.get_ui_constant('table_row_max_height', 50)
        except:
            min_height = 40
            max_height = 50
        
        return ft.DataTable(
            columns=self._get_columns_for_size("lg"),  
            rows=[],
            column_spacing=10,
            horizontal_margin=5,
            data_row_max_height=max_height,
            data_row_min_height=min_height,
            expand=True,  
            width=None,   
            divider_thickness=1,  
        )
    
    def _get_columns_for_size(self, size_category: str) -> List[ft.DataColumn]:

        config = self.column_configs.get(size_category, self.column_configs["lg"])
        columns = []
        
        if config.get("file", True):
            columns.append(ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("user", True):
            columns.append(ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("team", True):
            columns.append(ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("size", True):
            columns.append(ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("submitted", True):
            columns.append(ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("status", True):
            columns.append(ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)))
        
        return columns
    
    def create_table_row(self, file_data: Dict, size_category: str, 
                        on_file_select: Callable) -> ft.DataRow:
        """Create responsive table row with dynamic column visibility."""
        # Use dynamic column configuration if available
        config = getattr(self, 'current_column_config', None)
        if not config:
            config = self.column_configs.get(size_category, self.column_configs["lg"])
        
        file_size = file_data.get('file_size', 0)
        size_str = self.format_file_size(file_size)

        try:
            submit_date = datetime.fromisoformat(file_data['submission_date'])
            date_str = submit_date.strftime("%m/%d %H:%M")
        except:
            date_str = "Unknown"
        
        original_filename = file_data.get('original_filename', 'Unknown')
        max_lengths = {'xs': 15, 'sm': 20, 'md': 25, 'lg': 30}
        max_filename_length = max_lengths.get(size_category, 30)
        display_filename = self._limit_filename_display(original_filename, max_filename_length)
        
        # Create status badge with proper styling
        status = file_data.get('status', 'pending')
        status_badge = self._create_status_badge(status)
        
        cells = []
        
        if config.get("file", True):
            cells.append(ft.DataCell(
                ft.Container(
                    content=ft.Text(
                        display_filename,
                        tooltip=original_filename,
                        size=14,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        weight=ft.FontWeight.W_500
                    ),
                    padding=ft.padding.symmetric(vertical=2)
                )
            ))
        
        if config.get("user", True):
            cells.append(ft.DataCell(
                ft.Text(file_data.get('user_id', 'Unknown'), size=14)
            ))
        
        if config.get("team", True):
            cells.append(ft.DataCell(
                ft.Text(file_data.get('user_team', 'Unknown'), size=14)
            ))
        
        if config.get("size", True):
            cells.append(ft.DataCell(
                ft.Text(size_str, size=14)
            ))
        
        if config.get("submitted", True):
            cells.append(ft.DataCell(
                ft.Text(date_str, size=14)
            ))
        
        if config.get("status", True):
            cells.append(ft.DataCell(status_badge))
        
        return ft.DataRow(
            cells=cells,
            on_select_changed=lambda e, data=file_data: on_file_select(data)
        )
    
    def _limit_filename_display(self, filename: str, max_length: int) -> str:
        """Limit filename display length with smart truncation."""
        if len(filename) <= max_length:
            return filename
        
        if max_length > 10:
            start_len = max_length // 2 - 2
            end_len = max_length - start_len - 3
            return f"{filename[:start_len]}...{filename[-end_len:]}"
        else:
            return filename[:max_length-3] + "..."
    
    def _create_status_badge(self, status: str) -> ft.Container:
        """Create color-coded status badge."""
        status_configs = {
            'pending_admin': {'text': 'PENDING ADMIN', 'color': ft.Colors.ORANGE},
            'pending_team_leader': {'text': 'PENDING TL', 'color': ft.Colors.ORANGE},
            'pending': {'text': 'PENDING', 'color': ft.Colors.ORANGE},
            'approved': {'text': 'APPROVED', 'color': ft.Colors.GREEN},
            'rejected_admin': {'text': 'REJECTED', 'color': ft.Colors.RED},
            'rejected_team_leader': {'text': 'REJECTED', 'color': ft.Colors.RED_700}
        }
        
        config = status_configs.get(status, {'text': status.upper(), 'color': ft.Colors.GREY})
        
        return ft.Container(
            content=ft.Text(
                config['text'], 
                color=ft.Colors.WHITE, 
                size=10, 
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=config['color'],
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            alignment=ft.alignment.center
        )
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:

        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def add_empty_table_row(self, table: ft.DataTable):

        num_columns = len(table.columns)
        empty_cells = []
        empty_cells.append(ft.DataCell(
            ft.Text("No pending files found", style=ft.TextStyle(italic=True))
        ))
        
        for i in range(num_columns - 1):
            empty_cells.append(ft.DataCell(ft.Text("")))
        
        table.rows.append(ft.DataRow(cells=empty_cells))
    
    def show_table_error(self, table: ft.DataTable, error_msg: str):

        table.rows.clear()
        
        error_cells = [ft.DataCell(ft.Text(f"Error loading files: {error_msg}", color=ft.Colors.RED))]
        for i in range(len(table.columns) - 1):
            error_cells.append(ft.DataCell(ft.Text("")))
        
        table.rows.append(ft.DataRow(cells=error_cells))
    
    def get_size_category_from_page_width(self, page_width: Optional[int]) -> str:

        try:
            width = page_width if page_width else 1200
            if width < 600:
                return "xs"
            elif width < 900:
                return "sm"
            elif width < 1200:
                return "md"
            else:
                return "lg"
        except Exception:
            return "lg"  # Safe default


class FileFilter:
    """Helper class for filtering and sorting file data."""
    
    def __init__(self, enhanced_logger):

        self.enhanced_logger = enhanced_logger
    
    def apply_search_filter(self, files: List[Dict], search_query: str) -> List[Dict]:

        if not search_query:
            return files
        
        search_lower = search_query.lower()
        return [
            f for f in files
            if (search_lower in f.get('original_filename', '').lower() or
                search_lower in f.get('user_id', '').lower() or
                search_lower in f.get('description', '').lower())
        ]
    
    def apply_team_filter(self, files: List[Dict], team_filter: str) -> List[Dict]:

        if team_filter == "ALL":
            return files
        
        return [f for f in files if f.get('user_team', '') == team_filter]
    
    def sort_files(self, files: List[Dict], sort_option: str) -> List[Dict]:

        try:
            if sort_option == "filename":
                return sorted(files, key=lambda x: x.get('original_filename', '').lower())
            elif sort_option == "user_id":
                return sorted(files, key=lambda x: x.get('user_id', '').lower())
            elif sort_option == "file_size":
                return sorted(files, key=lambda x: x.get('file_size', 0), reverse=True)
            else:  # submission_date
                return sorted(files, key=lambda x: x.get('submission_date', ''), reverse=True)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error sorting files: {e}")
            return files
    
    def apply_filters(self, files: List[Dict], search_query: str, 
                     team_filter: str, sort_option: str) -> List[Dict]:

        filtered_files = self.apply_search_filter(files, search_query)
        filtered_files = self.apply_team_filter(filtered_files, team_filter)
        return self.sort_files(filtered_files, sort_option)
