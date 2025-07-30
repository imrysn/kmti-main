import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
from utils.session_logger import log_activity

TEAMS_FILE = "data/teams.json"
SETTINGS_FILE = "data/settings.json"


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


def load_settings():
    defaults = {
        "maintenance": False,
        "system_name": "KMTI System",
        "theme": "Light",
        "font_size": "Medium",
        "session_timeout": 30,
        "password_min_length": 8,
    }
    data = load_json(SETTINGS_FILE, {})
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


# ========== Main Settings Page ==========
def system_settings(content: ft.Column, username: Optional[str]):
    content.controls.clear()
    settings_data = load_settings()

    # Track current section
    state = {"selected": "Application"}
    right_panel = ft.Container(expand=True, bgcolor="white", border_radius=12, padding=20)

    # ------------ Pages ------------

    # --- Application Page ---
    def application_page():
        maintenance_switch = ft.Switch(
            label="Maintenance Mode",
            value=settings_data.get("maintenance", False),
        )
        system_name_field = ft.TextField(
            label="System Name",
            value=settings_data.get("system_name", "KMTI System"),
            width=300
        )

        def save_app_settings(e):
            settings_data["maintenance"] = maintenance_switch.value
            settings_data["system_name"] = system_name_field.value.strip() or "KMTI System"
            save_settings(settings_data)
            log_activity(username, "Updated Application settings")
            content.page.snack_bar = ft.SnackBar(ft.Text("Application settings saved!"), open=True)
            content.page.update()

        return ft.Column([
            ft.Text("Application Settings", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            maintenance_switch,
            system_name_field,
            ft.ElevatedButton("Save Settings", on_click=save_app_settings),
        ], spacing=20, expand=True)

    # --- Team Management Page ---
    team_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Actions"))
        ],
        rows=[]
    )
    new_team_field = ft.TextField(label="New Team", width=250)

    def refresh_team_table():
        team_table.rows.clear()

        for team in load_teams():
            team_field = ft.TextField(value=team, expand=True, disabled=True)

            def toggle_edit(edit_btn, save_btn, field):
                field.disabled = False
                field.update()
                edit_btn.visible = False
                save_btn.visible = True
                edit_btn.update()
                save_btn.update()

            def save_changes(e, old=team, field=team_field, edit_btn=None, save_btn=None):
                new_name = field.value.strip()
                if new_name and new_name != old:
                    teams = load_teams()
                    if old in teams:
                        teams[teams.index(old)] = new_name
                        save_teams(teams)
                        log_activity(username, f"Renamed team '{old}' to '{new_name}'")
                # disable back
                field.disabled = True
                if edit_btn and save_btn:
                    edit_btn.visible = True
                    save_btn.visible = False
                refresh_team_table()

            def delete_team(e, tname=team):
                teams = load_teams()
                if tname in teams:
                    teams.remove(tname)
                    save_teams(teams)
                    log_activity(username, f"Deleted team '{tname}'")
                refresh_team_table()

            edit_btn = ft.IconButton(ft.Icons.EDIT, tooltip="Edit")
            save_btn = ft.IconButton(ft.Icons.SAVE, tooltip="Save", visible=False)

            edit_btn.on_click = lambda e, eb=edit_btn, sb=save_btn, f=team_field: toggle_edit(eb, sb, f)
            save_btn.on_click = lambda e, f=team_field, eb=edit_btn, sb=save_btn: save_changes(e, team, f, eb, sb)

            team_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(team_field),
                        ft.DataCell(
                            ft.Row(
                                [
                                    edit_btn,
                                    save_btn,
                                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, tooltip="Delete",
                                                  on_click=lambda e: delete_team(e)),
                                ]
                            )
                        )
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
            log_activity(username, f"Added new team '{name}'")
        new_team_field.value = ""
        refresh_team_table()

    def team_page():
        refresh_team_table()
        return ft.Column([
            ft.Text("Teams", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Row([new_team_field, ft.ElevatedButton("Add Team", on_click=add_team)]),
            team_table
        ], spacing=20, expand=True)

    # --- User Preferences Page ---
    theme_dropdown = ft.Dropdown(
        label="Theme",
        value=settings_data.get("theme", "Light"),
        options=[ft.dropdown.Option("Light"), ft.dropdown.Option("Dark")],
        width=200
    )
    font_dropdown = ft.Dropdown(
        label="Font Size",
        value=settings_data.get("font_size", "Medium"),
        options=[ft.dropdown.Option("Small"), ft.dropdown.Option("Medium"), ft.dropdown.Option("Large")],
        width=200
    )

    def save_preferences(e):
        settings_data["theme"] = theme_dropdown.value
        settings_data["font_size"] = font_dropdown.value
        save_settings(settings_data)
        log_activity(username, "Updated User Preferences")
        content.page.snack_bar = ft.SnackBar(ft.Text("Preferences saved!"), open=True)
        content.page.update()

    def preferences_page():
        return ft.Column([
            ft.Text("User Preferences", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            theme_dropdown,
            font_dropdown,
            ft.ElevatedButton("Save Preferences", on_click=save_preferences)
        ], spacing=20, expand=True)

    # --- Security Page ---
    timeout_field = ft.TextField(
        label="Session Timeout (minutes)",
        value=str(settings_data.get("session_timeout", 30)),
        width=200
    )
    pw_length_field = ft.TextField(
        label="Password Minimum Length",
        value=str(settings_data.get("password_min_length", 8)),
        width=200
    )

    def save_security(e):
        settings_data["session_timeout"] = int(timeout_field.value or 30)
        settings_data["password_min_length"] = int(pw_length_field.value or 8)
        save_settings(settings_data)
        log_activity(username, "Updated Security settings")
        content.page.snack_bar = ft.SnackBar(ft.Text("Security settings saved!"), open=True)
        content.page.update()

    def security_page():
        return ft.Column([
            ft.Text("Security Settings", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            timeout_field,
            pw_length_field,
            ft.ElevatedButton("Save Security Settings", on_click=save_security)
        ], spacing=20, expand=True)

    # --- About Page ---
    def about_page():
        return ft.Column([
            ft.Text("About KMTI System", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Version: 1.0.0"),
            ft.Text("Developed by: Your Team"),
            ft.Text("Description: Local File System Data Management Tool"),
        ], spacing=20, expand=True)

    # ------------ Navigation ------------

    sections = [
        "Application",
        "Teams",
        "User Preferences",
        "Security",
        "About"
    ]

    def render_sidebar():
        sidebar_column = ft.Column(
            controls=[ft.Text("Preferences", weight=FontWeight.BOLD, size=18), ft.Divider()],
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        for s in sections:
            is_selected = (s == state["selected"])
            btn = ft.TextButton(
                text=s,
                style=ft.ButtonStyle(
                    color="#000000" if is_selected else "#007BFFFF",
                    bgcolor="#0234BBFF" if is_selected else "#F5F5F7",
                ),
                on_click=lambda e, sec=s: show_section(sec),
            )
            container = ft.Container(
                content=btn,
                border_radius=5,
                padding=5,
                width=180,
                bgcolor="#007BFFFF" if is_selected else None
            )
            sidebar_column.controls.append(container)

        return ft.Container(
            bgcolor="#F5F5F7",
            width=200,
            content=sidebar_column,
            padding=20,
        )

    def show_section(section_name):
        state["selected"] = section_name
        if section_name == "Application":
            right_panel.content = application_page()
        elif section_name == "Teams":
            right_panel.content = team_page()
        elif section_name == "User Preferences":
            right_panel.content = preferences_page()
        elif section_name == "Security":
            right_panel.content = security_page()
        elif section_name == "About":
            right_panel.content = about_page()

        # Re-render sidebar for dynamic highlight
        layout.controls.clear()
        layout.controls.append(render_sidebar())
        layout.controls.append(right_panel)
        content.update()

    layout = ft.Row(expand=True)
    content.controls.append(layout)

    # Initial
    show_section(state["selected"])
    content.update()
