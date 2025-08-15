# Three-Role System Implementation - Complete Documentation

## 🎯 Overview

This document provides a complete overview of the three-role system implementation for the KMTI Data Management System. The system implements proper role-based access control, workflow management, and UI color coding for **Admin**, **Team Leader**, and **User** roles.

---

## 🔐 Role Definitions

### 1. **Admin** (🔴 Red - `ft.Colors.RED`)
- **Panel Access**: Admin Panel only
- **Permissions**: Full system access
  - Can approve/reject files at admin level
  - Can view files with status `pending_admin`
  - Can manage users, view all logs, system settings
  - Access to all teams and files
  - Can view comprehensive system statistics

### 2. **Team Leader** (🔵 Blue - `ft.Colors.BLUE`)  
- **Panel Access**: Team Leader Panel only
- **Permissions**: Team-limited access
  - Can approve/reject files at team leader level
  - Can view files with status `pending_team_leader` from their team only
  - Cannot access admin functions
  - Limited to files from their assigned team
  - Can add comments to files

### 3. **User** (🟢 Green - `ft.Colors.GREEN`)
- **Panel Access**: User Panel only
- **Permissions**: Basic access
  - Can upload files and view "My Files"
  - Can submit files for team leader review (status changes to `pending_team_leader`)
  - Cannot approve/reject files
  - Cannot access admin or team leader functions
  - Can withdraw submissions before approval

---

## 📋 File Approval Workflow

```
┌─────────────┐    Submit for     ┌─────────────────────┐    TL Approve    ┌──────────────┐    Admin Approve    ┌──────────┐
│  my_files   │ ───Review──────► │ pending_team_leader │ ──────────────► │ pending_admin │ ─────────────────► │ approved │
└─────────────┘                  └─────────────────────┘                  └──────────────┘                     └──────────┘
                                            │                                       │
                                            │ TL Reject                             │ Admin Reject
                                            ▼                                       ▼
                                  ┌──────────────────────┐                ┌─────────────────┐
                                  │ rejected_team_leader │                │ rejected_admin  │
                                  └──────────────────────┘                └─────────────────┘
                                            │                                       │
                                            └───────── Can Resubmit ──────────────┘
```

### Status Definitions:
- **`my_files`**: Files uploaded by user, not yet submitted for review
- **`pending_team_leader`**: Submitted for team leader review
- **`pending_admin`**: Approved by team leader, pending admin review  
- **`approved`**: Final approval by admin, process complete
- **`rejected_team_leader`**: Rejected by team leader with reason
- **`rejected_admin`**: Rejected by admin with reason

---

## 🚪 Access Control Implementation

### Login System (`login_window.py`)
- **User Login**: Only users with `USER` role can access
- **Administrator Login**: Only `ADMIN` and `TEAM_LEADER` roles can access
- Role validation prevents cross-panel access
- Color-coded login type indicator

### Session Management (`main.py`)
- Role-based panel routing in `restore_session()`
- Proper role validation on session restore
- Automatic redirection to appropriate panel

### Panel Access Control
Each panel validates user roles on entry:
- **Admin Panel**: Requires `ADMIN` role exactly
- **Team Leader Panel**: Requires `TEAM_LEADER` role exactly  
- **User Panel**: Requires `USER` role exactly

---

## 🎨 UI Color Coding System

### Implementation (`admin/components/role_colors.py`)
```python
COLORS = {
    "ADMIN": ft.Colors.RED,
    "TEAM_LEADER": ft.Colors.BLUE, 
    "USER": ft.Colors.GREEN
}
```

### Usage Throughout System:
- **Login Screen**: Role type text color changes
- **Navigation Bars**: Role badges with appropriate colors
- **User Lists**: Role indicators in tables
- **Status Badges**: Consistent color scheme

---

## 📁 File Structure

### Core Files Modified/Created:
```
├── main.py                              # Updated role-based routing
├── login_window.py                      # Enhanced role validation & colors
├── admin_panel.py                       # Admin role verification
├── TLPanel.py                          # Team Leader role verification
├── user/user_panel.py                  # User role verification
├── utils/auth.py                       # Enhanced role-based authentication
├── admin/components/
│   ├── role_permissions.py             # Role permission definitions
│   ├── role_colors.py                  # Color management system
│   ├── team_leader_service.py          # TL-specific workflow functions
│   └── approval_actions.py             # Action handlers
└── services/approval_service.py        # Updated workflow statuses
```

---

## ⚙️ Technical Implementation Details

### 1. Authentication Enhancement
- `validate_login()` now enforces role-based access
- Admin/TL login requires `ADMIN` or `TEAM_LEADER` role
- User login requires `USER` role
- Cross-panel access attempts are blocked

### 2. Workflow Engine
- Team Leader Service handles TL-specific operations
- Status transitions follow strict rules
- File queuing system updated for multi-stage approval

### 3. Permission System
- Enum-based role definitions
- Granular permission checking
- Access level enforcement (full/team_limited/none)

### 4. UI Consistency
- Centralized color management
- Role badge creation utilities
- Consistent styling across all panels

---

## 🧪 Testing

### Test Script: `test_complete_three_role_system.py`
Comprehensive testing suite covering:
- ✅ User creation for all roles
- ✅ Role permission validation
- ✅ Color system verification
- ✅ Authentication testing
- ✅ Approval workflow validation
- ✅ Status transition testing

### Test Users Created:
- **Admin**: `admin` / `admin123`
- **Team Leader**: `teamleader` / `tl123`  
- **User**: `user1` / `user123`

---

## 🚀 Usage Instructions

### 1. Run Tests
```bash
python test_complete_three_role_system.py
```

### 2. Start Application
```bash
python main.py
```

### 3. Login Process
1. **For Users**: Use "User" login mode (green)
2. **For Admin/Team Leaders**: Use "Administrator" login mode (red)
3. System automatically routes to appropriate panel based on role

### 4. File Approval Process
1. **User** uploads files (status: `my_files`)
2. **User** submits for review (status: `pending_team_leader`)
3. **Team Leader** approves/rejects (status: `pending_admin` or `rejected_team_leader`)
4. **Admin** gives final approval/rejection (status: `approved` or `rejected_admin`)

---

## 🔧 Configuration

### Environment Setup
- Ensure `\\KMTI-NAS\Shared\data\users.json` is accessible
- Create necessary data directories
- Run test script to set up test users

### Role Assignment
Users are assigned roles in `users.json`:
```json
{
  "email@domain.com": {
    "username": "username",
    "role": "ADMIN|TEAM_LEADER|USER",
    "team_tags": ["TEAM_NAME"]
  }
}
```

---

## ⚡ Key Features

### ✅ Implemented Features
- **Role-Based Access Control**: Complete enforcement
- **Multi-Stage Workflow**: Team Leader → Admin approval
- **Color-Coded UI**: Consistent throughout system  
- **Panel Isolation**: No cross-role access
- **Status Management**: Proper workflow transitions
- **Session Security**: Role validation on restore
- **Comprehensive Testing**: Full test coverage

### 🔒 Security Features
- Role validation on every panel access
- Session-based access control
- Proper authentication flow
- Cross-role access prevention
- Secure password hashing

---

## 📈 Benefits

1. **Clear Hierarchy**: Defined approval chain
2. **Security**: Role-based access prevents unauthorized actions
3. **User Experience**: Color coding for easy role identification
4. **Scalability**: Easy to add more roles or modify permissions
5. **Maintainability**: Modular design with clear separation of concerns
6. **Audit Trail**: Complete workflow tracking

---

## 🎯 Summary

This implementation provides a complete three-role system with:
- **Proper access control** preventing unauthorized panel access
- **Structured workflow** ensuring files go through correct approval stages
- **Visual consistency** with role-based color coding
- **Comprehensive testing** to ensure system reliability
- **Clear documentation** for maintenance and future development

The system is now production-ready with all requirements fully implemented and tested.
