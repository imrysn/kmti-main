# Three-Role System Implementation Patch

## Overview
This patch implements a complete 3-role system for the KMTI Data Management System with proper access control, workflow, and UI elements.

## Roles and Access Control

### 1. **Admin** (Red - ft.Colors.RED)
- **Panel Access**: Admin Panel only
- **Permissions**: Full system access
  - Can approve/reject files at admin level
  - Can view files pending admin approval
  - Can manage users, view all logs, system settings
  - Access to all teams and files

### 2. **Team Leader** (Blue - ft.Colors.BLUE)  
- **Panel Access**: Team Leader Panel only
- **Permissions**: Team-limited access
  - Can approve/reject files at team leader level
  - Can view files pending team leader approval from their team only
  - Cannot access admin functions
  - Limited to their assigned team

### 3. **User** (Green - ft.Colors.GREEN)
- **Panel Access**: User Panel only
- **Permissions**: Basic access
  - Can upload files and view "My Files"
  - Can submit files for team leader review
  - Cannot approve/reject files
  - Cannot access admin or team leader functions

## File Approval Workflow
```
my_files → pending_team_leader → pending_admin → approved
                ↓                     ↓
        rejected_team_leader    rejected_admin
```

## Implementation Files
- Main entry point: `main.py` (updated routing)
- Login system: `login_window.py` (role-based routing)
- Authentication: `utils/auth.py` (role validation)
- Role permissions: `admin/components/role_permissions.py`
- Team Leader service: `admin/components/team_leader_service.py`
- Approval workflow: `services/approval_service.py`

## Status Transitions
- Users submit files: `status = 'pending_team_leader'`
- Team Leader approves: `status = 'pending_admin'`
- Team Leader rejects: `status = 'rejected_team_leader'`
- Admin approves: `status = 'approved'`
- Admin rejects: `status = 'rejected_admin'`
