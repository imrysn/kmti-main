import json
import os
from pathlib import Path
from typing import Dict, List
from .path_config import DATA_PATHS

# Your existing CONFIG_FILE - now using centralized path config
CONFIG_FILE = DATA_PATHS.config_file

def get_base_dir():
    """Your existing function - kept unchanged for backward compatibility"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                path = data.get("base_dir", "")
                if path and os.path.exists(path):
                    return Path(path)
        except:
            pass
    # fallback: default path
    return Path("data/config.json")

class EnhancedConfig:
    """Enhanced configuration class that extends your existing config"""
    
    def __init__(self):
        self.base_dir = get_base_dir()  # Use your existing function
        
        # Load your existing config
        self.config_data = self._load_config_file()
        
        # Define secure paths using centralized configuration
        self.data_dir = Path(DATA_PATHS.LOCAL_BASE)
        self.uploads_dir = Path(DATA_PATHS.uploads_dir)
        self.logs_dir = Path(DATA_PATHS.local_logs_dir)
        
        # Security: Define allowed directories for file operations
        self.allowed_directories = [
            self.base_dir,
            self.data_dir,
            self.uploads_dir,
            self.logs_dir,
            Path("storage") if Path("storage").exists() else self.data_dir / "storage"
        ]
        
        # UI Constants for consistent styling
        self.ui_constants = {
            'max_filename_lengths': {'xs': 15, 'sm': 20, 'md': 25, 'lg': 30},
            'table_row_min_height': 40,
            'table_row_max_height': 50,
            'stat_card_width': 110,
            'stat_card_height': 80,
            'search_field_width': 200,
            'dropdown_width': 150,
            'preview_panel_padding': 15,
            'button_border_radius': 5
        }
        
        # File operation constants
        self.file_constants = {
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'allowed_extensions': {
                '.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', 
                '.png', '.gif', '.zip', '.csv', '.xlsx', '.ppt', '.pptx'
            },
            'cache_ttl_seconds': 300,  # 5 minutes
            'max_cache_size': 100
        }
        
        # Column configurations for responsive table
        self.column_configs = {
            'xs': {'file': True, 'user': False, 'team': False, 'size': False, 'submitted': False, 'status': True},
            'sm': {'file': True, 'user': True, 'team': False, 'size': False, 'submitted': False, 'status': True},
            'md': {'file': True, 'user': True, 'team': True, 'size': False, 'submitted': True, 'status': True},
            'lg': {'file': True, 'user': True, 'team': True, 'size': True, 'submitted': True, 'status': True}
        }
    
    def _load_config_file(self) -> Dict:
        """Load your existing config file with error handling"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def get_allowed_directories(self) -> List[Path]:
        """Get list of directories allowed for file operations (security)"""
        return self.allowed_directories
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories (security check)"""
        try:
            resolved_path = path.resolve()
            for allowed_dir in self.allowed_directories:
                try:
                    allowed_dir = allowed_dir.resolve()
                    resolved_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def get_ui_constant(self, key: str, default=None):
        """Get UI constant value"""
        return self.ui_constants.get(key, default)
    
    def get_file_constant(self, key: str, default=None):
        """Get file operation constant"""
        return self.file_constants.get(key, default)
    
    def get_column_config(self, size_category: str) -> Dict[str, bool]:
        """Get column configuration for responsive table"""
        return self.column_configs.get(size_category, self.column_configs['lg'])
    
    def update_config(self, key: str, value):
        """Update configuration value and save to file"""
        self.config_data[key] = value
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_config_value(self, key: str, default=None):
        """Get configuration value from your existing config"""
        return self.config_data.get(key, default)

# Create global instance for easy access
_config_instance = None

def get_config() -> EnhancedConfig:
    """Get global configuration instance (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnhancedConfig()
    return _config_instance

# Maintain backward compatibility - your existing function works unchanged
# New enhanced functions available via get_config()