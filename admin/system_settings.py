import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
from utils.session_logger import log_activity

TEAMS_FILE = "data/teams.json"


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


# ========== Main Settings Page ==========
def system_settings(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    # Track current section
    state = {"selected": "Teams"}
    right_panel = ft.Container(expand=True, bgcolor="white", border_radius=12, padding=20)

    # ------------ Pages ------------

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

            edit_btn = ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Edit")
            save_btn = ft.IconButton(ft.Icons.SAVE_OUTLINED, tooltip="Save", visible=False)

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
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINED,
                                        icon_color=ft.Colors.RED,
                                        tooltip="Delete",
                                        on_click=lambda e, tn=team: delete_team(e, tn),
                                    ),
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

    # --- About Page ---
    def about_page():
        return ft.Column([
            ft.Text("About KMTI Data Management System", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Version: 1.0.0"),
            ft.Text("Developed by: OJT Team"),
            ft.Text("Description: Local File System Data Management Tool"),
        ], spacing=20, expand=True)

    # ------------ Navigation ------------
    sections = [
        "Teams",
        "About"
    ]

    # Containers for buttons, so we can update highlight without re-rendering
    sidebar_buttons = {}

    def show_section(section_name):
        # Update selected section
        state["selected"] = section_name

        # Update button highlights (only change property, don't call update() yet)
        for sec, cont in sidebar_buttons.items():
            cont.bgcolor = "#007BFFFF" if sec == section_name else "#F5F5F7"

        # Update right panel content
        if section_name == "Teams":
            right_panel.content = team_page()
        elif section_name == "About":
            right_panel.content = about_page()

        # Update the whole content once
        content.update()


    # Sidebar with hover effects
    sidebar_column = ft.Column(
        spacing=5,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    for s in sections:
        is_selected = (s == state["selected"])
        btn = ft.TextButton(
            text=s,
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                       ft.ControlState.SELECTED: ft.Colors.WHITE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE,
                       ft.ControlState.PRESSED: ft.Colors.WHITE},
                bgcolor={ft.ControlState.HOVERED: "#339CFF",
                         ft.ControlState.SELECTED: "#007BFF"},
            ),
            on_click=lambda e, sec=s: show_section(sec),
            
        )
        container = ft.Container(
            content=btn,
            border_radius=5,
            padding=5,
            width=180,
            bgcolor="#007BFFFF" if is_selected else "#F5F5F7",
        )
        sidebar_buttons[s] = container
        sidebar_column.controls.append(container)

    sidebar = ft.Container(
        bgcolor="#F5F5F7",
        width=200,
        content=sidebar_column,
        padding=20,
        
    )

    # Layout: sidebar stays, right panel updates
    layout = ft.Row([sidebar, right_panel], expand=True)
    content.controls.append(layout)
     
    # Initial page
    show_section(state["selected"])
    content.update()
