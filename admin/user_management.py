import flet as ft
from flet import FontWeight, Colors
from typing import Optional
import json

def user_management(page: ft.Page, username: Optional[str]):
    def load_users():
        with open("data/users.json", "r") as f:
            return json.load(f)
    
    def view_user_profile(e):
        user_email = e.control.data
        # Implement user profile view
        
    users = load_users()
    user_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    for email, data in users.items():
        user_list.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(data['fullname'], weight=FontWeight.BOLD, size=16),
                            ft.Text(data['status'], color={
                                "Active": ft.Colors.GREEN,
                                "Inactive": ft.Colors.ORANGE,
                                "Banned": ft.Colors.RED
                            }.get(data['status'], ft.Colors.GREY))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(email),
                        ft.Text(f"Role: {data['role']}"),
                        ft.Text(f"Joined: {data['join_date']}"),
                        ft.Row([
                            ft.ElevatedButton("View Profile", on_click=view_user_profile, data=email),
                            ft.ElevatedButton("Reset Password", color=ft.Colors.AMBER),
                            ft.ElevatedButton("Edit", color=ft.Colors.BLUE),
                            ft.ElevatedButton("Delete", color=ft.Colors.RED)
                        ], spacing=5)
                    ], spacing=5),
                    padding=10
                )
            )
        )
    
    search_field = ft.TextField(label="Search users...", expand=True)
    
    page.add(
        ft.Column([
            ft.Row([
                search_field,
                ft.ElevatedButton("Add New User", icon=ft.Icons.ADD)
            ]),
            ft.Divider(),
            user_list
        ], expand=True)
    )