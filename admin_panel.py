import flet as ft
import json
from utils.logger import log_action
from flet import FontWeight, ScrollMode, CrossAxisAlignment, MainAxisAlignment, Colors
from typing import Optional

def admin_panel(page: ft.Page, username: Optional[str]):
    # Set page properties
    page.title = "Admin Dashboard"
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.START
    page.bgcolor = "#f5f5f5"
    page.padding = 20

    def logout(e):
        log_action(username, "Logged out")
        page.clean()
        from login_window import login_view
        login_view(page)

    def load_users():
        try:
            with open("data/users.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_logs():
        try:
            with open("data/logs/activity.log", "r") as f:
                return f.readlines()[-20:]  # Show last 20 logs
        except FileNotFoundError:
            return ["No activity logs found"]

    # Initialize content area
    content = ft.Column(scroll=ScrollMode.AUTO, expand=True)
    
    # Load data
    users = load_users()
    logs = load_logs()

    def get_user_status(data):
        return data.get('status', 'Unknown')

    def show_dashboard():
        content.controls.clear()
        
        # Dashboard Overview Cards
        total_users = len(users)
        active_users = sum(1 for u in users.values() if get_user_status(u) == 'Active')
        
        content.controls.extend([
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE, size=40),
                        ft.Text("Total Users", size=16),
                        ft.Text(str(total_users), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PERSON, size=40),
                        ft.Text("Active Users", size=16),
                        ft.Text(str(active_users), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.HISTORY, size=40),
                        ft.Text("Recent Activities", size=16),
                        ft.Text(str(len(logs)), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                )
            ], spacing=20),
            
            ft.Divider(height=40),
            
            # Recent Users Section
            ft.Text("Recent Users", size=20, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Name")),
                    ft.DataColumn(ft.Text("Email")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Actions"))
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(data.get('fullname', 'Unknown'))),
                            ft.DataCell(ft.Text(email)),
                            ft.DataCell(ft.Text(
                                get_user_status(data),
                                color={
                                    "Active": Colors.GREEN,
                                    "Inactive": Colors.ORANGE,
                                    "Banned": Colors.RED
                                }.get(get_user_status(data), Colors.GREY)
                            )),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.Icons.EDIT, tooltip="Edit"),
                                ft.IconButton(ft.Icons.LOCK_RESET, tooltip="Reset Password"),
                                ft.IconButton(ft.Icons.DELETE, tooltip="Delete", icon_color=Colors.RED)
                            ]))
                        ]
                    ) for email, data in list(users.items())[:5]  # Show only first 5 users
                ],
            ),
            
            ft.Divider(height=40),
            
            # Recent Activities Section
            ft.Text("Recent Activities", size=20, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.ListView(
                [ft.Text(line.strip()) for line in reversed(logs[-10:])],  # Show last 10 logs
                height=200,
                spacing=5
            )
        ])
        page.update()

    def show_user_management():
        content.controls.clear()
        
        search_field = ft.TextField(
            label="Search users...",
            width=300,
            suffix_icon=ft.Icons.SEARCH
        )
        
        user_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions"))
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(data.get('fullname', 'Unknown'))),
                        ft.DataCell(ft.Text(email)),
                        ft.DataCell(ft.Text(data.get('role', 'Unknown'))),
                        ft.DataCell(
                            ft.Text(
                                get_user_status(data),
                                color={
                                    "Active": Colors.GREEN,
                                    "Inactive": Colors.ORANGE,
                                    "Banned": Colors.RED
                                }.get(get_user_status(data), Colors.GREY)
                            )
                        ),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.EDIT, tooltip="Edit"),
                            ft.IconButton(ft.Icons.LOCK_RESET, tooltip="Reset Password"),
                            ft.IconButton(ft.Icons.DELETE, tooltip="Delete", icon_color=Colors.RED)
                        ]))

                    ]
                ) for email, data in users.items()
            ],
        )
        
        content.controls.extend([
            ft.Row([
                search_field,
                ft.ElevatedButton("Add New User", icon=ft.Icons.ADD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            user_table
        ])
        page.update()

    def show_activity_logs():
        content.controls.clear()
        
        log_view = ft.Column(
            [ft.Text(line.strip()) for line in reversed(logs)],
            spacing=5,
            scroll=ScrollMode.AUTO,
            expand=True
        )
        
        content.controls.extend([
            ft.Row([
                ft.TextField(
                    label="Filter logs...",
                    width=300,
                    suffix_icon=ft.Icons.FILTER_ALT
                ),
                ft.ElevatedButton("Export Logs", icon=ft.Icons.DOWNLOAD)
            ]),
            ft.Divider(),
            log_view
        ])
        page.update()

    def navigate_to_section(e):
        index = e.control.selected_index
        if index == 0:
            show_dashboard()
        elif index == 1:
            show_user_management()
        elif index == 2:
            show_activity_logs()

    # Create navigation rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.Column([
            ft.Text("Admin Panel", weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Hi, {username}", size=12),
            ft.TextButton("Logout", on_click=logout)
        ]),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINED,
                selected_icon=ft.Icons.PEOPLE,
                label="User Management"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.HISTORY_OUTLINED,
                selected_icon=ft.Icons.HISTORY,
                label="Activity Logs"
            ),
        ],
        on_change=navigate_to_section
    )

    # Initial view - show dashboard
    show_dashboard()

    # Add everything to page
    page.add(
        ft.Row([
            nav_rail,
            ft.VerticalDivider(width=1),
            ft.Container(content=content, expand=True, padding=20)
        ], expand=True)
    )

    log_action(username, "Logged into admin panel")