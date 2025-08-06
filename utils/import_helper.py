"""Common utility functions for handling imports in the project"""
import os
import sys

def setup_imports():
    """Add the project root to Python path"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

def get_project_root():
    """Get the absolute path to the project root directory"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
