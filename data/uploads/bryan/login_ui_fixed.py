import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os

def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1+radius, y1,
        x1+radius, y1,
        x2-radius, y1,
        x2-radius, y1,
        x2, y1,
        x2, y1+radius,
        x2, y1+radius,
        x2, y2-radius,
        x2, y2-radius,
        x2, y2,
        x2-radius, y2,
        x2-radius, y2,
        x1+radius, y2,
        x1+radius, y2,
        x1, y2,
        x1, y2-radius,
        x1, y2-radius,
        x1, y1+radius,
        x1, y1+radius,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

class FileExplorerWindow:
    def __init__(self, root, username, user_type):
        self.root = root
        self.username = username
        self.user_type = user_type
        
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.root.title(f"File Explorer - {user_type}")
        self.setup_file_explorer()
    
    def setup_file_explorer(self):
        # Top menu bar
        self.create_top_menu()
        
        # Navigation bar
        self.create_navigation_bar()
        
        # Main content area with sidebar
        self.create_main_content()
    
    def create_top_menu(self):
        # Top menu frame
        menu_frame = tk.Frame(self.root, bg='#4a4a4a', height=40)
        menu_frame.pack(fill='x', side='top')
        menu_frame.pack_propagate(False)
        
        # Left side frame for menu items
        left_frame = tk.Frame(menu_frame, bg='#4a4a4a')
        left_frame.pack(side='left', padx=15)
        
        # Admin menu items (only show for administrators)
        if self.user_type == "Administrator":
            admin_menus = ["Data Management", "User Management", "Activity Logs", "System Settings"]
            for menu_item in admin_menus:
                menu_button = tk.Label(left_frame, text=menu_item, bg='#4a4a4a', fg='white', 
                                     font=("Arial", 11), padx=15, pady=12, cursor="hand2")
                menu_button.pack(side='left')
                menu_button.bind("<Button-1>", lambda e, item=menu_item: self.handle_admin_menu(item))
                
                # Add hover effects
                menu_button.bind("<Enter>", lambda e, btn=menu_button: btn.config(bg='#5a5a5a'))
                menu_button.bind("<Leave>", lambda e, btn=menu_button: btn.config(bg='#4a4a4a'))
        else:
            # Regular Help button for users
            help_button = tk.Label(left_frame, text="Help", bg='#4a4a4a', fg='white', 
                                  font=("Arial", 11), padx=15, pady=12)
            help_button.pack(side='left')
        
        # Right side frame for user info and logout
        right_frame = tk.Frame(menu_frame, bg='#4a4a4a')
        right_frame.pack(side='right', padx=15)
        
        # Hi, User label (clickable)
        user_label = tk.Label(right_frame, text=f"Hi, {self.username}", bg='#4a4a4a', fg='white', 
                             font=("Arial", 11), padx=10, pady=12, cursor="hand2")
        user_label.bind("<Button-1>", self.show_profile)
        user_label.pack(side='left')
        
        # Logout button
        logout_button = tk.Label(right_frame, text="Logout", bg='#4a4a4a', fg='white', 
                                font=("Arial", 11), padx=10, pady=12, cursor="hand2")
        logout_button.bind("<Button-1>", self.logout)
        logout_button.pack(side='right')
    
    def create_navigation_bar(self):
        # Navigation frame
        nav_frame = tk.Frame(self.root, bg='#e0e0e0', height=50)
        nav_frame.pack(fill='x', side='top')
        nav_frame.pack_propagate(False)
        
        # Navigation buttons frame
        nav_buttons_frame = tk.Frame(nav_frame, bg='#e0e0e0')
        nav_buttons_frame.pack(side='left', padx=10, pady=10)
        
        # Back button
        back_btn = tk.Button(nav_buttons_frame, text="←", font=("Arial", 12), width=3, height=1)
        back_btn.pack(side='left', padx=2)
        
        # Forward button
        forward_btn = tk.Button(nav_buttons_frame, text="→", font=("Arial", 12), width=3, height=1)
        forward_btn.pack(side='left', padx=2)
        
        # Up button
        up_btn = tk.Button(nav_buttons_frame, text="↑", font=("Arial", 12), width=3, height=1)
        up_btn.pack(side='left', padx=2)
        
        # Admin action buttons (only show for administrators)
        if self.user_type == "Administrator":
            # Upload button with dropdown
            upload_frame = tk.Frame(nav_buttons_frame, bg='#e0e0e0')
            upload_frame.pack(side='left', padx=10)
            
            upload_btn = tk.Button(upload_frame, text="Upload ▼", font=("Arial", 10), 
                                 bg='white', relief='solid', bd=1, padx=10, pady=2,
                                 command=self.show_upload_menu)
            upload_btn.pack()
            
            # Create button with dropdown
            create_frame = tk.Frame(nav_buttons_frame, bg='#e0e0e0')
            create_frame.pack(side='left', padx=5)
            
            create_btn = tk.Button(create_frame, text="Create ▼", font=("Arial", 10), 
                                 bg='white', relief='solid', bd=1, padx=10, pady=2,
                                 command=self.show_create_menu)
            create_btn.pack()
        
        # For Admin: Don't show address bar, center the search
        if self.user_type == "Administrator":
            # Spacer to center search
            spacer_frame = tk.Frame(nav_frame, bg='#e0e0e0')
            spacer_frame.pack(side='left', fill='x', expand=True)
            
            # Search frame (centered)
            search_frame = tk.Frame(nav_frame, bg='#e0e0e0')
            search_frame.pack(side='right', expand=True, padx=10, pady=10)
        else:
            # Address bar frame (for regular users)
            address_frame = tk.Frame(nav_frame, bg='#e0e0e0')
            address_frame.pack(side='left', fill='x', expand=True, padx=(10, 0), pady=10)
            
            # Address bar
            self.address_bar = tk.Entry(address_frame, font=("Arial", 10), bg='white')
            self.address_bar.insert(0, "X:\\PROJECTS\\KUSAKABE\\")
            self.address_bar.pack(side='left', fill='x', expand=True)
            
            # Search frame
            search_frame = tk.Frame(nav_frame, bg='#e0e0e0')
            search_frame.pack(side='right', padx=10, pady=10)
        
        # Search entry
        self.search_entry = tk.Entry(search_frame, font=("Arial", 10), width=35, fg='gray')
        if self.user_type == "Administrator":
            # No placeholder for admin
            self.search_entry.config(fg='black')
        else:
            self.search_entry.insert(0, "Search...")
            self.search_entry.bind("<FocusIn>", self.clear_search_placeholder)
            self.search_entry.bind("<FocusOut>", self.add_search_placeholder)
        self.search_entry.pack(side='left')
        
        # Search button
        search_btn = tk.Button(search_frame, text="🔍", font=("Arial", 10), width=3)
        search_btn.pack(side='left', padx=(2, 0))
    
    def create_main_content(self):
        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True)
        
        # Left sidebar (for both admin and users)
        left_sidebar = tk.Frame(main_frame, bg='#e8e8e8', width=200)
        left_sidebar.pack(side='left', fill='y')
        left_sidebar.pack_propagate(False)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg='#f0f0f0')
        content_frame.pack(side='left', fill='both', expand=True)
        
        # File area (left side of content)
        if self.user_type == "Administrator":
            file_frame = tk.Frame(content_frame, bg='#f0f0f0', width=500)
        else:
            file_frame = tk.Frame(content_frame, bg='#f0f0f0', width=400)
        file_frame.pack(side='left', fill='y', padx=20, pady=20)
        file_frame.pack_propagate(False)
        
        # Create folder icons
        self.create_folders(file_frame)
        
        # Preview area (right side)
        if self.user_type == "Administrator":
            preview_frame = tk.Frame(content_frame, bg='#f0f0f0')
        else:
            preview_frame = tk.Frame(content_frame, bg='#f0f0f0', width=380)
        preview_frame.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=20)
        if self.user_type != "Administrator":
            preview_frame.pack_propagate(False)
        
        # Preview box
        preview_box = tk.Frame(preview_frame, bg='white', relief='solid', bd=1)
        preview_box.pack(fill='both', expand=True)
        
        # Preview text
        preview_label = tk.Label(preview_box, text="Select file to preview.", 
                               bg='white', fg='#666666', font=("Arial", 12),
                               wraplength=450, justify='center')
        preview_label.place(relx=0.5, rely=0.5, anchor='center')
    
    def create_folders(self, parent):
        # Folder data
        folders = [
            ("AGCC Project", 0, 0),
            ("DAIICHI", 1, 0),
            ("KMTI PJ", 2, 0),
            ("KUSAKABE", 3, 0),
            ("SPECIAL\nPROJECT_S\nOLIDWORKS\nData", 0, 1),
            ("WINDSMILE", 1, 1),
            ("Minatogumi", 2, 1)
        ]
        
        for folder_name, col, row in folders:
            # Create folder frame
            folder_frame = tk.Frame(parent, bg='#f0f0f0')
            folder_frame.grid(row=row, column=col, padx=20, pady=20, sticky='n')
            
            # Folder icon (black rectangle to represent folder)
            folder_canvas = tk.Canvas(folder_frame, width=80, height=60, bg='#f0f0f0', highlightthickness=0)
            folder_canvas.pack()
            
            # Draw folder icon
            folder_canvas.create_rectangle(10, 15, 70, 50, fill='black', outline='black')
            folder_canvas.create_rectangle(10, 10, 30, 15, fill='black', outline='black')
            
            # Folder name
            name_label = tk.Label(folder_frame, text=folder_name, bg='#f0f0f0', 
                                font=("Arial", 9), justify='center')
            name_label.pack(pady=(5, 0))
    
    def handle_admin_menu(self, menu_item):
        # Handle admin menu clicks
        messagebox.showinfo("Admin Menu", f"You clicked on: {menu_item}")
        # Add your admin functionality here
    
    def show_upload_menu(self):
        # Show upload options
        messagebox.showinfo("Upload", "Upload menu options would appear here")
    
    def show_create_menu(self):
        # Show create options
        messagebox.showinfo("Create", "Create menu options would appear here")
    
    def clear_search_placeholder(self, event):
        if self.search_entry.get() == "Search...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='black')
    
    def add_search_placeholder(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search...")
            self.search_entry.config(fg='gray')
    
    def show_profile(self, event):
        # Create profile window
        ProfileWindow(self.root, self.username, self.user_type)
    
    def logout(self, event):
        # Return to login screen
        LoginApp(self.root)

class ProfileWindow:
    def __init__(self, parent_root, username, user_type):
        self.parent_root = parent_root
        self.username = username
        self.user_type = user_type
        
        # Clear the main window
        for widget in self.parent_root.winfo_children():
            widget.destroy()
            
        self.parent_root.title("User Profile")
        self.setup_profile()
    
    def setup_profile(self):
        # Top menu bar (simplified)
        self.create_top_menu()
        
        # Main profile content
        self.create_profile_content()
    
    def create_top_menu(self):
        # Top menu frame
        menu_frame = tk.Frame(self.parent_root, bg='#4a4a4a', height=40)
        menu_frame.pack(fill='x', side='top')
        menu_frame.pack_propagate(False)
        
        # Help button on the left
        help_button = tk.Label(menu_frame, text="Help", bg='#4a4a4a', fg='white', 
                              font=("Arial", 11), padx=15, pady=12)
        help_button.pack(side='left')
        
        # Right side frame for logout
        right_frame = tk.Frame(menu_frame, bg='#4a4a4a')
        right_frame.pack(side='right', padx=15)
        
        # Logout button
        logout_button = tk.Label(right_frame, text="Logout", bg='#4a4a4a', fg='white', 
                                font=("Arial", 11), padx=10, pady=12, cursor="hand2")
        logout_button.bind("<Button-1>", self.logout)
        logout_button.pack(side='right')
    
    def create_profile_content(self):
        # Main content frame
        main_frame = tk.Frame(self.parent_root, bg='#e0e0e0')
        main_frame.pack(fill='both', expand=True)
        
        # Back button
        back_frame = tk.Frame(main_frame, bg='#e0e0e0')
        back_frame.pack(fill='x', padx=20, pady=20)
        
        back_button = tk.Button(back_frame, text="←", font=("Arial", 16), width=3, height=1,
                               command=self.go_back)
        back_button.pack(side='left')
        
        # Content container
        content_frame = tk.Frame(main_frame, bg='#e0e0e0')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Left sidebar with user info
        left_sidebar = tk.Frame(content_frame, bg='#e0e0e0', width=300)
        left_sidebar.pack(side='left', fill='y', padx=(0, 20))
        left_sidebar.pack_propagate(False)
        
        # User avatar (circular placeholder)
        avatar_frame = tk.Frame(left_sidebar, bg='#e0e0e0')
        avatar_frame.pack(pady=(20, 10))
        
        # Create circular avatar
        avatar_canvas = tk.Canvas(avatar_frame, width=150, height=150, bg='#e0e0e0', highlightthickness=0)
        avatar_canvas.pack()
        
        # Draw circular avatar (simplified representation)
        avatar_canvas.create_oval(10, 10, 140, 140, fill='#87CEEB', outline='#87CEEB')
        avatar_canvas.create_oval(50, 30, 100, 80, fill='#DEB887', outline='#DEB887')  # Face
        avatar_canvas.create_oval(40, 90, 110, 130, fill='#4169E1', outline='#4169E1')  # Body
        avatar_canvas.create_text(75, 75, text="👤", font=("Arial", 40), fill='white')
        
        # User type label
        user_type_label = tk.Label(left_sidebar, text=self.user_type, bg='#e0e0e0', 
                                  font=("Arial", 14, "bold"))
        user_type_label.pack(pady=5)
        
        # Username label
        username_label = tk.Label(left_sidebar, text=self.username, bg='#e0e0e0', 
                                 font=("Arial", 12))
        username_label.pack(pady=5)
        
        # Email label (placeholder)
        email = f"{self.username}@gmail.com" if self.username != "admin" else "admin@company.com"
        email_label = tk.Label(left_sidebar, text=email, bg='#e0e0e0', 
                              font=("Arial", 10), fg='gray')
        email_label.pack(pady=5)
        
        # Sidebar menu
        menu_frame = tk.Frame(left_sidebar, bg='#e0e0e0')
        menu_frame.pack(fill='x', pady=20)
        
        # Profile button (selected)
        profile_btn = tk.Button(menu_frame, text="Profile", font=("Arial", 11), 
                               bg='#a0a0a0', fg='black', relief='flat', width=15, height=2)
        profile_btn.pack(fill='x', pady=2)
        
        # Files button
        files_btn = tk.Button(menu_frame, text="Files", font=("Arial", 11), 
                             bg='#e0e0e0', fg='black', relief='flat', width=15, height=2,
                             command=self.go_back)
        files_btn.pack(fill='x', pady=2)
        
        # Right content area
        right_content = tk.Frame(content_frame, bg='white', relief='solid', bd=1)
        right_content.pack(side='right', fill='both', expand=True)
        
        # Profile details container
        details_frame = tk.Frame(right_content, bg='white')
        details_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Profile information
        self.create_profile_details(details_frame)
    
    def create_profile_details(self, parent):
        # Get user details based on username
        if self.username == "admin":
            full_name = "Administrator"
            email = "admin@company.com"
            join_date = "January 1, 2024"
        else:
            full_name = "Nicolas Ayin"  # Default user details as shown in image
            email = "Nicolasyin@gmail.com"
            join_date = "July 16, 2025"
        
        # Create a grid for profile information
        info_frame = tk.Frame(parent, bg='white')
        info_frame.pack(fill='x', pady=20)
        
        # Full Name
        tk.Label(info_frame, text="Full Name:", font=("Arial", 12), bg='white').grid(
            row=0, column=0, sticky='w', padx=20, pady=15)
        tk.Label(info_frame, text=full_name, font=("Arial", 12), bg='white').grid(
            row=0, column=1, sticky='w', padx=20, pady=15)
        
        # Join Date (right aligned)
        tk.Label(info_frame, text="Join Date:", font=("Arial", 12), bg='white').grid(
            row=0, column=2, sticky='w', padx=(100, 20), pady=15)
        tk.Label(info_frame, text=join_date, font=("Arial", 12), bg='white').grid(
            row=0, column=3, sticky='w', padx=20, pady=15)
        
        # Email
        tk.Label(info_frame, text="Email:", font=("Arial", 12), bg='white').grid(
            row=1, column=0, sticky='w', padx=20, pady=15)
        tk.Label(info_frame, text=email, font=("Arial", 12), bg='white').grid(
            row=1, column=1, sticky='w', padx=20, pady=15)
        
        # Role
        tk.Label(info_frame, text="Role:", font=("Arial", 12), bg='white').grid(
            row=2, column=0, sticky='w', padx=20, pady=15)
        tk.Label(info_frame, text=self.user_type, font=("Arial", 12), bg='white').grid(
            row=2, column=1, sticky='w', padx=20, pady=15)
        
        # Edit Profile button
        button_frame = tk.Frame(parent, bg='white')
        button_frame.pack(pady=30)
        
        edit_btn = tk.Button(button_frame, text="Edit Profile", font=("Arial", 11), 
                            bg='white', fg='black', relief='solid', bd=1, 
                            padx=20, pady=8, cursor="hand2",
                            command=self.edit_profile)
        edit_btn.pack()
    
    def edit_profile(self):
        messagebox.showinfo("Edit Profile", "Edit profile functionality would be implemented here.")
    
    def go_back(self):
        # Return to file explorer
        FileExplorerWindow(self.parent_root, self.username, self.user_type)
    
    def logout(self, event):
        # Return to login screen
        LoginApp(self.parent_root)

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#dcdcdc')
        
        self.is_admin_mode = False
        self.menu_frame = None
        
        self.setup_ui()

    def setup_ui(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Always create menu bar for both user and admin modes
        self.create_menu_bar()

        # Logo
        self.logo = self.load_logo()
        if self.logo:
            self.logo_label = tk.Label(self.root, image=self.logo, bg='#dcdcdc')
            self.logo_label.image = self.logo
            self.logo_label.place(relx=0.5, rely=0.21, anchor="center")
        else:
            self.draw_logo_placeholder()

        # Canvas for rounded login box
        self.login_canvas = tk.Canvas(self.root, width=370, height=260, bg='#dcdcdc', highlightthickness=0)
        self.login_canvas.place(relx=0.5, rely=0.5, anchor="center")
        round_rectangle(self.login_canvas, 5, 5, 365, 255, radius=30, fill='#bfbfbf', outline='#bfbfbf')

        # Place widgets on canvas
        login_type = "ADMINISTRATOR" if self.is_admin_mode else "USER"
        self.user_label = tk.Label(self.login_canvas, text=login_type, font=("Arial", 15, "bold"), bg='#bfbfbf')
        self.login_canvas.create_window(185, 40, window=self.user_label)

        self.username_entry = tk.Entry(self.login_canvas, font=("Arial", 12), width=26, fg='grey')
        self.username_entry.insert(0, "Username:")
        self.username_entry.bind("<FocusIn>", self.clear_username_placeholder)
        self.username_entry.bind("<FocusOut>", self.add_username_placeholder)
        self.login_canvas.create_window(185, 85, window=self.username_entry)

        self.password_entry = tk.Entry(self.login_canvas, font=("Arial", 12), width=26, fg='grey')
        self.password_entry.insert(0, "Password:")
        self.password_entry.bind("<FocusIn>", self.clear_password_placeholder)
        self.password_entry.bind("<FocusOut>", self.add_password_placeholder)
        self.login_canvas.create_window(185, 125, window=self.password_entry)

        self.login_button = tk.Button(self.login_canvas, text="Login", font=("Arial", 13, "bold"), 
                                    bg='#262626', fg='white', width=14, command=self.login)
        self.login_canvas.create_window(185, 170, window=self.login_button)

        # Reset password (only show for user login)
        if not self.is_admin_mode:
            self.reset_label = tk.Label(self.login_canvas, text="Reset password", font=("Arial", 10), 
                                      fg='blue', bg='#bfbfbf', cursor="hand2")
            self.login_canvas.create_window(185, 200, window=self.reset_label)

        # Bottom link
        if self.is_admin_mode:
            link_text = "Login as User"
            self.bottom_label = tk.Label(self.root, text=link_text, font=("Arial", 13), bg='#dcdcdc', 
                                       fg='black', cursor="hand2")
            self.bottom_label.bind("<Button-1>", self.switch_to_user)
        else:
            link_text = "Login as Administrator"
            self.bottom_label = tk.Label(self.root, text=link_text, font=("Arial", 13), bg='#dcdcdc', 
                                       fg='black', cursor="hand2")
            self.bottom_label.bind("<Button-1>", self.switch_to_admin)
            
        self.bottom_label.place(relx=0.5, rely=0.96, anchor="center")

        self.login_button.focus_set()

    def create_menu_bar(self):
        # Create a frame for the menu bar
        self.menu_frame = tk.Frame(self.root, bg='#4a4a4a', height=35)
        self.menu_frame.pack(fill='x', side='top')
        self.menu_frame.pack_propagate(False)
        
        # Help button
        help_button = tk.Label(self.menu_frame, text="Help", bg='#4a4a4a', fg='white', 
                              font=("Arial", 11), padx=15, pady=8)
        help_button.pack(side='left')

    def clear_username_placeholder(self, event):
        if self.username_entry.get() == "Username:":
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg='black')

    def add_username_placeholder(self, event):
        if not self.username_entry.get():
            self.username_entry.insert(0, "Username:")
            self.username_entry.config(fg='grey')

    def clear_password_placeholder(self, event):
        if self.password_entry.get() == "Password:":
            self.password_entry.delete(0, tk.END)
            self.password_entry.config(show='*', fg='black')

    def add_password_placeholder(self, event):
        if not self.password_entry.get():
            self.password_entry.config(show='', fg='grey')
            self.password_entry.insert(0, "Password:")

    def draw_logo_placeholder(self):
        canvas = tk.Canvas(self.root, width=250, height=120, bg='#dcdcdc', highlightthickness=0)
        canvas.place(relx=0.5, rely=0.21, anchor="center")
        # Draw KMTI logo with gear
        canvas.create_oval(75, 30, 175, 130, fill='red', width=8)
        canvas.create_oval(100, 55, 150, 105, fill='blue')
        canvas.create_text(125, 140, text="KMTI", font=("Arial", 20, "bold"), fill='blue')

    def load_logo(self):
        try:
            if os.path.exists("logo (3).png"):
                img = Image.open("logo (3).png")
                img.thumbnail((250, 120), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            else:
                return None
        except Exception as e:
            print(f"Error loading logo: {e}")
            return None

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "Username:" or not username:
            messagebox.showerror("Error", "Please enter your username.")
            return
        if password == "Password:" or not password:
            messagebox.showerror("Error", "Please enter your password.")
            return
        
        # Define credentials with their specific roles
        admin_credentials = {
            "admin": "admin123"
        }
        
        user_credentials = {
            "user": "user123"
        }
        
        # Check if trying to login as admin
        if self.is_admin_mode:
            if username in admin_credentials and password == admin_credentials[username]:
                # Successful admin login
                FileExplorerWindow(self.root, username, "Administrator")
            else:
                messagebox.showerror("Login Failed", "Invalid administrator credentials.")
        else:
            # Check if trying to login as user
            if username in user_credentials and password == user_credentials[username]:
                # Successful user login
                FileExplorerWindow(self.root, username, "User")
            else:
                messagebox.showerror("Login Failed", "Invalid user credentials.")

    def switch_to_admin(self, event):
        self.is_admin_mode = True
        self.setup_ui()

    def switch_to_user(self, event):
        self.is_admin_mode = False
        self.setup_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()