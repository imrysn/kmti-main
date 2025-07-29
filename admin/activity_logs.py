import flet as ft
import json
import os
import asyncio
from datetime import datetime

LOG_FILE = "data/activity_logs.json"


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def activity_logs(content: ft.Column, username: str):
    # Clear previous content
    content.controls.clear()

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date/Time")),
            ft.DataColumn(ft.Text("Username")),
            ft.DataColumn(ft.Text("Full Name")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Description")),
        ],
        rows=[]
    )

    def refresh_table():
        table.rows.clear()
        logs = load_logs()

        # Sort safely, using empty string if datetime is missing
        logs_sorted = sorted(logs, key=lambda x: x.get("datetime", ""), reverse=True)

        for log in logs_sorted:
            dt_str = log.get("datetime", "")
            try:
                dt_display = (
                    datetime.fromisoformat(dt_str).strftime("%Y-%m-%d %H:%M:%S")
                    if dt_str
                    else "-"
                )
            except Exception:
                dt_display = "-"

            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(dt_display)),
                        ft.DataCell(ft.Text(log.get("username", ""))),
                        ft.DataCell(ft.Text(log.get("fullname", ""))),
                        ft.DataCell(ft.Text(log.get("email", ""))),
                        ft.DataCell(ft.Text(log.get("role", ""))),
                        ft.DataCell(ft.Text(log.get("description", ""))),
                    ]
                )
            )

        content.update()

    # Wrap table in a centered Row so it always stays in the center
    centered_table = ft.Row(
        controls=[table],
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True
    )

    container = ft.Container(
        content=ft.Column(
            [
                ft.Text(f"Activity Logs - {username}", size=24, weight="bold"),
                ft.Divider(),
                centered_table,
            ],
            spacing=20,
            expand=True
        ),
        expand=True,
        padding=20,
    )

    content.controls.append(container)
    refresh_table()

    # Auto refresh every 5 seconds using asyncio
    async def periodic_refresh():
        while True:
            await asyncio.sleep(5)
            refresh_table()

    # Schedule the refresh task
    content.page.run_task(periodic_refresh)
