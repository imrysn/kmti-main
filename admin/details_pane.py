import flet as ft
from pathlib import Path
from datetime import datetime


class DetailsPane(ft.Container):
    def __init__(self):
        super().__init__(
            width=300,
            content=ft.Column(spacing=10),
            visible=False
        )
        self.details_content = self.content

    def update_details(self, item):
        self.details_content.controls.clear()

        if isinstance(item, Path):
            name = item.name
            file_type = "Folder" if item.is_dir() else "File"
            size = "-" if item.is_dir() else f"{round(item.stat().st_size / 1024, 2)}"
            modified = datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(item, dict):
            name = item.get("name", "-")
            file_type = item.get("type", "-")
            size = item.get("size", "-")
            modified = item.get("modified", "-")
        else:
            name = file_type = size = modified = "-"

        self.details_content.controls.append(
            ft.Text(f"Name: {name}", size=14, weight=ft.FontWeight.BOLD)
        )
        self.details_content.controls.append(ft.Text(f"Type: {file_type}"))
        self.details_content.controls.append(ft.Text(f"Size: {size} KB"))
        self.details_content.controls.append(ft.Text(f"Date Modified: {modified}"))

        if self.page is not None and self.details_content.page is not None:
            self.details_content.update()

        self.visible = True
        if self.page is not None:
            self.update()

    def clean(self):
        self.details_content.controls.clear()
        if self.details_content.page is not None:
            self.details_content.update()

        self.visible = False
        if self.page is not None:
            self.update()
