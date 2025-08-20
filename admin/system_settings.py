import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
from utils.session_logger import log_activity

TEAMS_FILE = r"\\KMTI-NAS\Shared\data\teams.json"
CONFIG_FILE = r"\\KMTI-NAS\Shared\data\config.json"

# ========== Helpers for JSON ==========
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_teams():
    return load_json(TEAMS_FILE, [])


def save_teams(teams):
    save_json(TEAMS_FILE, teams)

def load_config():
    return load_json(CONFIG_FILE, {"base_dir": ""})

def save_config(config):
    save_json(CONFIG_FILE, config)

# ========== Main Settings Page ==========
def system_settings(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    # ------------ Team Management Section ------------
    team_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Actions"))
        ],
        rows=[]
    )
    new_team_field = ft.TextField(label=" Add New Team", width=250)

    def refresh_team_table():
        team_table.rows.clear()

        teams = load_teams()
        for index, team in enumerate(teams):
            team_field = ft.TextField(value=team, expand=True, disabled=True)

            edit_btn = ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Edit")
            save_btn = ft.IconButton(ft.Icons.SAVE_OUTLINED, tooltip="Save", visible=False)
            delete_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINED,
                icon_color=ft.Colors.RED,
                tooltip="Delete",
            )

            # Define button handlers inside a function to capture correct variables
            def make_handlers(old_team, field, eb, sb, db):
                def toggle_edit(_):
                    field.disabled = False
                    field.update()
                    eb.visible = False
                    sb.visible = True
                    eb.update()
                    sb.update()

                def save_changes(_):
                    new_name = field.value.strip()
                    if new_name and new_name != old_team:
                        teams_list = load_teams()
                        if old_team in teams_list:
                            teams_list[teams_list.index(old_team)] = new_name
                            save_teams(teams_list)
                            log_activity(username, f"Renamed team '{old_team}' to '{new_name}'")
                    # Lock the field again
                    field.disabled = True
                    eb.visible = True
                    sb.visible = False
                    field.update()
                    eb.update()
                    sb.update()
                    refresh_team_table()

                def delete_team(_):
                    teams_list = load_teams()
                    if old_team in teams_list:
                        teams_list.remove(old_team)
                        save_teams(teams_list)
                        log_activity(username, f"Deleted team '{old_team}'")
                    refresh_team_table()

                eb.on_click = toggle_edit
                sb.on_click = save_changes
                db.on_click = delete_team

            # Apply handlers with correct scope
            make_handlers(team, team_field, edit_btn, save_btn, delete_btn)

            team_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(team_field),
                        ft.DataCell(
                            ft.Row(
                                [
                                    edit_btn,
                                    save_btn,
                                    delete_btn,
                                ]
                            )
                        ),
                    ]
                )
            )

        content.update()

    def add_team(e):
        name = new_team_field.value.strip()
        if not name:
            return
        teams = load_teams()
        if name not in teams:
            teams.append(name)
            save_teams(teams)
            log_activity(username, f"'{name}' Team Added")
        new_team_field.value = ""
        refresh_team_table()

    # Initialize team table
    refresh_team_table()

    # ------------ Directory Settings Section ------------
    config = load_config()
    current_path = config.get("base_dir", "")

    path_field = ft.TextField(
        label="Base Directory Path",
        value=current_path,
        expand=True
    )

    def browse_folder(_):
        def on_result(e: ft.FilePickerResultEvent):
            if e.path:
                path_field.value = e.path
                path_field.update()
        file_picker = ft.FilePicker(on_result=on_result)
        content.page.overlay.append(file_picker)
        content.page.update()
        file_picker.get_directory_path()

    def save_directory(_):
        new_path = path_field.value.strip()
        if new_path and os.path.exists(new_path):
            config["base_dir"] = new_path
            save_config(config)
            log_activity(username, f"Changed base directory to {new_path}")
            dlg = ft.AlertDialog(
                title=ft.Text("Directory Saved"),
                content=ft.Text("Base directory updated successfully.")
            )
            content.page.dialog = dlg
            dlg.open = True
            content.page.update()
        else:
            dlg = ft.AlertDialog(
                title=ft.Text("Invalid Path"),
                content=ft.Text("The entered path does not exist.")
            )
            content.page.dialog = dlg
            dlg.open = True
            content.page.update()

    # ------------ Main Layout (Single Scrollable Page) ------------
    main_content = ft.Column(
        controls=[
            # Page Header
            ft.Container(
                content=ft.Text("System Settings", size=28, weight=FontWeight.BOLD),
                margin=ft.margin.only(bottom=50)
            ),
            
            # Team Management Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Team Management", size=22, weight=FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row(
                        [
                            new_team_field,
                            ft.ElevatedButton("Add Team", on_click=add_team,
                                              style=ft.ButtonStyle(
                                                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                        ft.ControlState.HOVERED: ft.Colors.BLUE},
                                                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                                        ft.ControlState.HOVERED: ft.Colors.WHITE},
                                                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                                                shape=ft.RoundedRectangleBorder(radius=5))),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),  
                    ft.Container(
                        content=team_table,
                        alignment=ft.alignment.center
                    )
                ], spacing=10),
                bgcolor="white",
                border_radius=12,
                padding=20,
                margin=ft.margin.only(bottom=50),
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )

            ),
            
            # Directory Settings Section
            ft.Container(
                content=ft.Column([
                    ft.Text("Base Directory Settings", size=22, weight=FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([
                        path_field,
                        ft.ElevatedButton("Browse", on_click=browse_folder,
                                          style=ft.ButtonStyle(
                                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                    ft.ControlState.HOVERED: ft.Colors.BLUE},
                                            color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                                    ft.ControlState.HOVERED: ft.Colors.WHITE},
                                            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                                            shape=ft.RoundedRectangleBorder(radius=5))),
                        ft.ElevatedButton("Save", on_click=save_directory,
                                          style=ft.ButtonStyle(
                                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                    ft.ControlState.HOVERED: ft.Colors.GREEN},
                                            color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                                    ft.ControlState.HOVERED: ft.Colors.WHITE},
                                            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN)},
                                            shape=ft.RoundedRectangleBorder(radius=5))),
                    ]),
                    ft.Container(height=10),  # Spacer
                    ft.Text(
                        "This directory will be used as the root for file management.",
                        size=14,
                        italic=True,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=10),
                bgcolor="white",
                border_radius=12,
                padding=20,
                margin=ft.margin.only(bottom=50),
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )
            ),
            
            # About Section
            ft.Container(
                content=ft.Column([
                    ft.Text("About KMTI File Management System", size=22, weight=FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Version: 1.0.0", size=16),
                    ft.Text("Developed by: OJT Team", size=16),
                    ft.Text("Description: Local File System Data Management System", size=16),
                ], spacing=15),
                bgcolor="white",
                border_radius=12,
                padding=20,
                margin=ft.margin.only(bottom=50),
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )
            ),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO, 
        expand=True
    )

    page_container = ft.Container(
        content=main_content,
        padding=50,
        margin=ft.margin.symmetric(horizontal=250), 
        expand=True
    )

    content.controls.append(page_container)
    content.update()
