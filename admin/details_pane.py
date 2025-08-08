import flet as ft
from pathlib import Path
from datetime import datetime
import os


class DetailsPane(ft.Container):
    def __init__(self):
        super().__init__(
            width=300,
            content=ft.Column(spacing=15, tight=True),
            visible=False,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            padding=20,
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            ),
        )
        self.details_content = self.content

    def get_file_type(self, item: Path):
        """Determine the file type based on extension"""
        if item.is_dir():
            return "Folder"
        
        ext = item.suffix.lower()
        file_types = {
            '.pdf': 'PDF File',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.csv': 'CSV File',
            '.txt': 'Text Document',
            '.png': 'PNG Image',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.gif': 'GIF Image',
            '.bmp': 'Bitmap Image',
            '.svg': 'SVG Image',
            '.mp4': 'MP4 Video',
            '.avi': 'AVI Video',
            '.mov': 'QuickTime Video',
            '.mp3': 'MP3 Audio',
            '.wav': 'WAV Audio',
            '.zip': 'ZIP Archive',
            '.rar': 'RAR Archive',
            '.7z': '7-Zip Archive',
            '.exe': 'Application',
            '.msi': 'Windows Installer',
            '.py': 'Python File',
            '.js': 'JavaScript File',
            '.html': 'HTML Document',
            '.css': 'CSS File',
            '.json': 'JSON File',
            '.xml': 'XML File',
            '.sql': 'SQL File',
            '.dwg': 'AutoCAD Drawing',
            '.icd': 'ICD File',
            '.ppt': 'PowerPoint Presentation',
            '.pptx': 'PowerPoint Presentation',
        }
        
        return file_types.get(ext, f'{ext.upper()[1:]} File' if ext else 'File')

    def format_file_size(self, size_bytes):
        """Format file size in appropriate units"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        # Format with appropriate decimal places
        if unit_index == 0:  # Bytes
            return f"{int(size)} {units[unit_index]}"
        elif size >= 100:
            return f"{size:.0f} {units[unit_index]}"
        elif size >= 10:
            return f"{size:.1f} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"

    def format_date(self, timestamp):
        """Format date in user-friendly format"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%m/%d/%Y %I:%M %p')
        except:
            return "Unknown"

    def create_detail_row(self, label, value, is_header=False):
        """Create a detail row with consistent styling"""
        if is_header:
            return ft.Container(
                content=ft.Text(
                    label, 
                    size=16, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK
                ),
                margin=ft.margin.only(bottom=10)
            )
        else:
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        label, 
                        size=12, 
                        color=ft.Colors.GREY_700,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Text(
                        str(value), 
                        size=14, 
                        color=ft.Colors.BLACK,
                        selectable=True
                    )
                ], spacing=2),
                margin=ft.margin.only(bottom=8)
            )

    def update_details(self, item):
        """Update the details panel with file/folder information"""
        self.details_content.controls.clear()

        if isinstance(item, Path) and item.exists():
            try:
                # Get file stats
                stat = item.stat()
                
                # Basic information
                name = item.name
                file_type = self.get_file_type(item)
                
                # Size calculation
                if item.is_dir():
                    size_display = "—"
                else:
                    size_display = self.format_file_size(stat.st_size)
                
                # Date information
                date_modified = self.format_date(stat.st_mtime)
                
                # File location (show parent directory)
                file_location = str(item.parent)
                
                # Add header
                self.details_content.controls.append(
                    self.create_detail_row("Details", "", is_header=True)
                )
                
                # Add details
                self.details_content.controls.append(
                    self.create_detail_row("Type", file_type)
                )
                
                self.details_content.controls.append(
                    self.create_detail_row("Size", size_display)
                )
                
                self.details_content.controls.append(
                    self.create_detail_row("File location", file_location)
                )
                
                self.details_content.controls.append(
                    self.create_detail_row("Date modified", date_modified)
                )
                
                # Add file name at the bottom for files
                if not item.is_dir():
                    self.details_content.controls.append(
                        ft.Divider(height=1, color=ft.Colors.GREY_300)
                    )
                    self.details_content.controls.append(
                        self.create_detail_row("File name", name)
                    )

            except Exception as e:
                print(f"[ERROR] Failed to get file details: {e}")
                self.details_content.controls.append(
                    ft.Text(f"Error loading details: {e}", color=ft.Colors.RED)
                )

        elif isinstance(item, dict):
            # Handle dictionary input (existing functionality)
            name = item.get("name", "—")
            file_type = item.get("type", "—")
            size = item.get("size", "—")
            modified = item.get("modified", "—")

            self.details_content.controls.append(
                self.create_detail_row("Details", "", is_header=True)
            )
            self.details_content.controls.append(
                self.create_detail_row("Type", file_type)
            )
            self.details_content.controls.append(
                self.create_detail_row("Size", f"{size} KB" if size != "—" else "—")
            )
            self.details_content.controls.append(
                self.create_detail_row("Date Modified", modified)
            )
        else:
            # Invalid item
            self.details_content.controls.append(
                ft.Text("No item selected", color=ft.Colors.GREY_600)
            )

        # Update the UI
        if self.page is not None and self.details_content.page is not None:
            self.details_content.update()

        self.visible = True
        if self.page is not None:
            self.update()

    def clean(self):
        """Clear the details panel"""
        self.details_content.controls.clear()
        if self.details_content.page is not None:
            self.details_content.update()

        self.visible = False
        if self.page is not None:
            self.update()