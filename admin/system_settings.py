import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
from utils.session_logger import log_activity

TEAMS_FILE = "data/teams.json"
CONFIG_FILE = "data/config.json"

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

# ========== Enhanced Settings Page (Fixed for current system) ==========
def system_settings(content: ft.Column, username: Optional[str]):
    """Enhanced system settings with corrected service integration"""
    content.controls.clear()

    # Get hybrid app if available
    try:
        from main import get_hybrid_app
        hybrid_app = get_hybrid_app(content.page)
    except Exception as e:
        print(f"⚠️ Could not get hybrid app: {e}")
        hybrid_app = None

    # Track current section
    state = {"selected": "Teams"}
    right_panel = ft.Container(expand=True, bgcolor="white", border_radius=12, padding=20)

    # System status header
    system_status = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.CLOUD_DONE if hybrid_app else ft.Icons.FOLDER, 
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                size=16
            ),
            ft.Text(
                f"{'NAS Database Connected' if hybrid_app else 'Legacy Mode Active'} - System Settings",
                size=12,
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                weight=ft.FontWeight.BOLD
            )
        ], spacing=5),
        bgcolor=ft.Colors.GREEN_100 if hybrid_app else ft.Colors.ORANGE_100,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=10,
        margin=ft.margin.only(bottom=20)
    )

    # ------------ Enhanced Team Management Page (Fixed) ------------
    team_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Actions"))
        ],
        rows=[]
    )
    new_team_field = ft.TextField(label="New Team", width=250)

    def load_teams_from_source():
        """Load teams using corrected method"""
        # Try legacy first since team_service doesn't exist
        legacy_teams = load_teams()
        
        # If empty, use default teams
        if not legacy_teams:
            default_teams = ["Minatogumi", "SOLID WORKS", "WINDSMILE", "AGCC Project", "KMTI PJ", "KUSAKABE", "ADMIN", "IT"]
            save_teams(default_teams)
            legacy_teams = default_teams
        
        print(f"🏢 Teams loaded: {len(legacy_teams)} teams")
        return legacy_teams

    def save_teams_to_source(teams):
        """Save teams using existing system"""
        # Always save to legacy JSON (since team_service doesn't exist)
        save_teams(teams)
        print("✅ Teams saved to JSON file")

    def refresh_team_table():
        team_table.rows.clear()

        teams = load_teams_from_source()
        for index, team in enumerate(teams):
            team_field = ft.TextField(value=team, expand=True, disabled=True)

            edit_btn = ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Edit")
            save_btn = ft.IconButton(ft.Icons.SAVE_OUTLINED, tooltip="Save", visible=False)
            delete_btn = ft.IconButton(
                ft.Icons.DELETE_OUTLINED,
                icon_color=ft.Colors.RED,
                tooltip="Delete",
            )

            # Define button handlers with proper scope
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
                        teams_list = load_teams_from_source()
                        if old_team in teams_list:
                            teams_list[teams_list.index(old_team)] = new_name
                            save_teams_to_source(teams_list)
                            
                            # Log activity using existing logger
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
                    teams_list = load_teams_from_source()
                    if old_team in teams_list:
                        teams_list.remove(old_team)
                        save_teams_to_source(teams_list)
                        
                        # Log activity using existing logger
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
                            ft.Row([
                                edit_btn,
                                save_btn,
                                delete_btn,
                            ])
                        ),
                    ]
                )
            )

        content.update()

    def add_team(e):
        name = new_team_field.value.strip()
        if not name:
            return
        
        teams = load_teams_from_source()
        if name not in teams:
            teams.append(name)
            save_teams_to_source(teams)
            
            # Log activity using existing logger
            log_activity(username, f"Added new team '{name}'")
        
        new_team_field.value = ""
        refresh_team_table()

    def team_page():
        refresh_team_table()
        teams_count = len(load_teams_from_source())
        
        return ft.Column([
            ft.Row([
                ft.Text("Team Management", size=22, weight=FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Text(f"{teams_count} teams", size=14, color=ft.Colors.GREY_600),
                new_team_field,
                ft.ElevatedButton("Add Team", on_click=add_team),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(
                content=team_table,
                height=400,
                bgcolor=ft.Colors.GREY_50,
                border_radius=8,
                padding=10
            )
        ], spacing=20, expand=True)

    # --- Enhanced Directory Settings Page ---
    def directory_page():
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
                
                # Log activity using existing logger
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

        return ft.Column([
            ft.Text("Base Directory Configuration", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Container(
                content=ft.Column([
                    ft.Text("Current Directory", size=16, weight=FontWeight.BOLD),
                    ft.Text(current_path if current_path else "No directory set", 
                           size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    ft.Row([
                        path_field,
                        ft.ElevatedButton("Browse", on_click=browse_folder),
                        ft.ElevatedButton("Save", on_click=save_directory),
                    ]),
                    ft.Container(height=10),
                    ft.Text(
                        "This directory will be used as the root for file management operations.",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=10),
                bgcolor=ft.Colors.GREY_50,
                border_radius=8,
                padding=20
            )
        ], spacing=20, expand=True)

    # --- Enhanced Database Status Page ---
    def database_page():
        """Show database connection and system information"""
        info_items = []
        
        if hybrid_app:
            try:
                # Get basic hybrid system info
                info_items.extend([
                    ("System Type", "Hybrid (SQLite + NAS)"),
                    ("Database Location", "\\\\KMTI-NAS\\SHARED\\data\\kmti.db"),
                    ("Connection Status", "✅ Connected"),
                ])
                
                # Try to get user count
                try:
                    all_users = hybrid_app.user_service.get_users()
                    info_items.append(("Total Users", str(len(all_users))))
                except Exception as e:
                    info_items.append(("Total Users", f"Error: {e}"))
                
                # Migration status
                migration_flag = "\\\\KMTI-NAS\\SHARED\\data\\.migration_done"
                migration_status = "✅ Completed" if os.path.exists(migration_flag) else "⚠️ Pending"
                info_items.append(("Data Migration", migration_status))
                
            except Exception as e:
                info_items.extend([
                    ("System Type", "Hybrid (Error)"),
                    ("Connection Status", f"❌ Error: {str(e)}"),
                ])
        else:
            # Legacy system info
            try:
                users_file = "data/users.json"
                logs_file = "data/logs/activity_logs.json"
                users = load_json(users_file, {})
                logs = load_json(logs_file, [])
                
                info_items.extend([
                    ("System Type", "Legacy (JSON Files)"),
                    ("Data Location", "Local data/ folder"),
                    ("Connection Status", "📁 File-based"),
                    ("Total Users", str(len(users))),
                    ("Total Activities", str(len(logs))),
                ])
            except Exception as e:
                info_items.append(("System Status", f"❌ Error: {str(e)}"))

        # Create info cards
        info_cards = []
        for key, value in info_items:
            # Color coding for status
            if "✅" in value:
                status_color = ft.Colors.GREEN
            elif "❌" in value:
                status_color = ft.Colors.RED
            elif "⚠️" in value:
                status_color = ft.Colors.ORANGE
            else:
                status_color = ft.Colors.BLUE

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(key, size=12, color=ft.Colors.GREY_600, weight=FontWeight.BOLD),
                        ft.Text(value, size=14, weight=FontWeight.NORMAL, color=status_color),
                    ], spacing=8),
                    padding=15,
                    width=300
                )
            )
            info_cards.append(card)

        # Test connection button
        def test_connection(_):
            if hybrid_app:
                try:
                    # Test hybrid connection by trying to get users
                    users = hybrid_app.user_service.get_users()
                    content.page.snack_bar = ft.SnackBar(
                        content=ft.Text("✅ NAS Database connection successful!"),
                        bgcolor=ft.Colors.GREEN
                    )
                except Exception as e:
                    content.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"❌ Connection test error: {str(e)}"),
                        bgcolor=ft.Colors.RED
                    )
            else:
                content.page.snack_bar = ft.SnackBar(
                    content=ft.Text("ℹ️ Legacy mode - no database connection to test"),
                    bgcolor=ft.Colors.ORANGE
                )
            
            content.page.snack_bar.open = True
            content.page.update()

        test_button = ft.ElevatedButton(
            "Test Connection",
            icon=ft.Icons.WIFI_PROTECTED_SETUP,
            on_click=test_connection,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE
            )
        )

        return ft.Column([
            ft.Row([
                ft.Text("Database & System Status", size=22, weight=FontWeight.BOLD),
                ft.Container(expand=True),
                test_button
            ]),
            ft.Divider(),
            ft.Row([
                ft.Column(info_cards[:len(info_cards)//2], spacing=10),
                ft.Column(info_cards[len(info_cards)//2:], spacing=10)
            ], spacing=20),
        ], spacing=20, expand=True)

    # --- Enhanced About Page ---
    def about_page():
        return ft.Column([
            ft.Text("About KMTI Data Management System", size=22, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Container(
                content=ft.Column([
                    ft.Text("System Information", size=18, weight=FontWeight.BOLD),
                    ft.Text("Version: 2.0.0 (Hybrid Edition)"),
                    ft.Text("Developed by: OJT Team"),
                    ft.Text("Description: Hybrid File System Data Management Tool"),
                    ft.Container(height=20),
                    ft.Text("Features", size=18, weight=FontWeight.BOLD),
                    ft.Text("• NAS Database Integration (SQLite)"),
                    ft.Text("• Legacy JSON File Support"),
                    ft.Text("• Multi-user File Approval System"),
                    ft.Text("• Role-based Access Control"),
                    ft.Text("• Real-time Activity Logging"),
                    ft.Text("• Team Management"),
                    ft.Container(height=20),
                    ft.Text("Current Mode", size=18, weight=FontWeight.BOLD),
                    ft.Text(f"{'🔗 Hybrid (NAS Connected)' if hybrid_app else '📁 Legacy (Local Files)'}",
                           color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                           weight=FontWeight.BOLD)
                ], spacing=8),
                bgcolor=ft.Colors.GREY_50,
                border_radius=8,
                padding=20
            )
        ], spacing=20, expand=True)

    # ------------ Enhanced Navigation ------------
    sections = [
        ("Teams", ft.Icons.GROUP),
        ("Directory", ft.Icons.FOLDER),
        ("Database", ft.Icons.STORAGE),
        ("About", ft.Icons.INFO)
    ]

    sidebar_buttons = {}

    def show_section(section_name):
        state["selected"] = section_name

        # Update button styles
        for sec, cont in sidebar_buttons.items():
            if sec == section_name:
                cont.bgcolor = "#007BFFFF"
                cont.border = ft.border.all(2, ft.Colors.BLUE_700)
            else:
                cont.bgcolor = "#F5F5F7"
                cont.border = None

        # Show appropriate content
        if section_name == "Teams":
            right_panel.content = team_page()
        elif section_name == "Directory":
            right_panel.content = directory_page()
        elif section_name == "Database":
            right_panel.content = database_page()
        elif section_name == "About":
            right_panel.content = about_page()

        content.update()

    # Enhanced sidebar with icons
    sidebar_column = ft.Column(
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    for section_name, icon in sections:
        is_selected = (section_name == state["selected"])
        
        btn = ft.TextButton(
            content=ft.Row([
                ft.Icon(icon, size=20),
                ft.Text(section_name, size=14)
            ], spacing=10),
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                       ft.ControlState.SELECTED: ft.Colors.WHITE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE,
                       ft.ControlState.PRESSED: ft.Colors.WHITE},
                bgcolor={ft.ControlState.HOVERED: "#339CFF",
                         ft.ControlState.SELECTED: "#007BFF"},
            ),
            on_click=lambda e, sec=section_name: show_section(sec),
        )
        
        container = ft.Container(
            content=btn,
            border_radius=8,
            padding=10,
            width=200,
            bgcolor="#007BFFFF" if is_selected else "#F5F5F7",
            border=ft.border.all(2, ft.Colors.BLUE_700) if is_selected else None
        )
        
        sidebar_buttons[section_name] = container
        sidebar_column.controls.append(container)

    sidebar = ft.Container(
        bgcolor="#F8F9FA",
        width=220,
        content=ft.Column([
            ft.Container(height=10),
            ft.Text("System Settings", size=16, weight=FontWeight.BOLD, 
                   color=ft.Colors.GREY_700, text_align="center"),
            ft.Divider(),
            sidebar_column
        ]),
        padding=15,
        border_radius=ft.border_radius.only(top_left=10, bottom_left=10)
    )

    # Main layout
    layout = ft.Row([sidebar, right_panel], expand=True)
    
    # Add system status at top
    content.controls.extend([
        system_status,
        layout
    ])

    # Initial page
    show_section(state["selected"])
    content.update()