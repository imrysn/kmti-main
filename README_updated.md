# 🗂️ KMTI Data Management System

A comprehensive file management and user administration system built with Python and Flet GUI framework.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flet](https://img.shields.io/badge/Flet-0.28.3-orange)

## ✨ Features

### 🔐 Authentication & User Management
- **Multi-role authentication** (Admin/User)
- **Session management** with remember me functionality
- **User profile management** with profile pictures
- **Password reset** and user administration

### 👨‍💼 Admin Panel
- **User management** - Create, edit, delete users
- **Activity monitoring** - Real-time user activity logs
- **System settings** and configuration
- **Data management** with export capabilities
- **Team management** functionality

### 👤 User Panel
- **File management** - Upload, download, rename, delete files
- **File metadata** - Add descriptions and tags to files
- **Profile management** - Update profile and profile picture
- **File browser** with advanced filtering and search
- **Drag-and-drop** file upload capability

### 🛠️ System Features
- **Real file storage** with metadata persistence
- **Activity logging** and audit trails
- **Session restoration** - Resume sessions on restart
- **Responsive UI** with modern design
- **Error handling** and user feedback

## 🏗️ Project Structure

```
kmti-main/
├── main.py                 # Application entry point
├── login_window.py         # Login interface
├── admin_panel.py          # Admin dashboard
├── admin/                  # Admin-specific modules
│   ├── activity_logs.py
│   ├── user_management.py
│   ├── data_management.py
│   └── system_settings.py
├── user/                   # User system
│   ├── components/         # UI components
│   │   ├── files_view.py
│   │   ├── profile_view.py
│   │   └── browser_view.py
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── user_panel.py      # User interface
├── utils/                 # Core utilities
│   ├── auth.py
│   ├── file_manager.py
│   ├── logger.py
│   └── session_logger.py
├── assets/               # Application assets
├── data/                 # Application data
│   ├── uploads/          # User file uploads
│   ├── logs/            # Activity logs
│   └── *.json           # Configuration files
└── cache/               # Application cache
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kmti-main
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📱 Usage

### First Time Setup
1. Launch the application
2. Toggle to "Administrator" login mode
3. Create your first admin account
4. Log in and start managing users and files

### Admin Features
- **Dashboard**: Overview of system statistics
- **User Management**: Add, edit, remove users
- **Activity Logs**: Monitor user activities
- **System Settings**: Configure application settings

### User Features
- **File Management**: Upload and organize files
- **Profile**: Update personal information and avatar
- **File Browser**: Navigate and search through files

## 🔧 Configuration

### Environment Setup
The application uses JSON configuration files in the `data/` directory:
- `config.json` - Application settings
- `users.json` - User accounts
- `teams.json` - Team configurations

### File Storage
User files are stored in `data/uploads/{username}/` with metadata in JSON format.

## 🧪 Development

### Running Tests
```bash
python test_file_system.py
```

### Project Cleanup
```bash
python cleanup_kmti.py
```

### Building for Production
The application is ready for production use. For deployment:
1. Ensure all dependencies are installed
2. Configure production settings in `data/config.json`
3. Set up proper file permissions for `data/` directory

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.14, or Linux
- **RAM**: 4GB
- **Storage**: 100MB + space for user files
- **Python**: 3.8+

### Recommended
- **RAM**: 8GB or more
- **Storage**: 1GB+ for optimal performance

## 🔐 Security Features

- **Password hashing** using bcrypt
- **Session management** with secure tokens
- **File access control** per user
- **Activity logging** for audit trails
- **Input validation** and sanitization

## 📞 Support

For support and questions:
- Check the `SYSTEM_STATUS.md` file for current system status
- Review activity logs in the admin panel
- Contact system administrator

## 📄 License

This project is developed for KMTI (Kolehiyo ng Makabagong Teknolohiyang Dalubhasa) internal use.

---

**Status**: ✅ Production Ready - All features implemented and tested
**Last Updated**: August 2025
**Version**: 1.0.0
