import flet as ft
import time
from pathlib import Path


class DetailsPane(ft.Column):
    def __init__(self):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.START
        self.spacing = 5
        self.expand = True

        self.title = ft.Text("Details", size=18, weight=ft.FontWeight.BOLD)
        self.divider = ft.Divider()
        self.details_content = ft.Column(alignment=ft.MainAxisAlignment.START, spacing=5)

        self.controls.extend([self.title, self.divider, self.details_content])

    def update_details(self, item: Path):
        """Updates the right-hand details panel."""
        self.details_content.controls.clear()
        if item.exists():
            self.details_content.controls.append(ft.Text(f"Name: {item.name}"))
            self.details_content.controls.append(ft.Text(f"Type: {'Folder' if item.is_dir() else 'File'}"))
            if item.is_file():
                self.details_content.controls.append(ft.Text(f"Size: {item.stat().st_size} bytes"))
            self.details_content.controls.append(ft.Text(f"Modified: {time.ctime(item.stat().st_mtime)}"))

        self.details_content.update()
