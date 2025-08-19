#!/usr/bin/env python3
"""
Temporary cleanup script to remove unnecessary files from KMTI project
"""

import os
import shutil
import glob

def remove_pycache_dirs(root_dir):
    """Remove all __pycache__ directories recursively"""
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing: {pycache_path}")
            shutil.rmtree(pycache_path)
            dirs.remove('__pycache__')  # Don't recurse into it

def remove_debug_scripts(root_dir):
    """Remove debug and temporary scripts"""
    debug_patterns = [
        'debug_*.py',
        'fix_*.py',
        'migrate_*.py',
        'validate_*.py',
        'check_*.py',
        'process_*.py',
        'quick_fix*.py',
        'implementation_summary.py'
    ]
    
    for pattern in debug_patterns:
        for file_path in glob.glob(os.path.join(root_dir, pattern)):
            if os.path.isfile(file_path):
                print(f"Removing debug script: {file_path}")
                os.remove(file_path)

def remove_backup_files(root_dir):
    """Remove backup files and old migration data"""
    # Remove .old files
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.old'):
                file_path = os.path.join(root, file)
                print(f"Removing backup file: {file_path}")
                os.remove(file_path)
    
    # Remove backup directories with old data
    backup_dir = os.path.join(root_dir, 'backup')
    if os.path.exists(backup_dir):
        # Keep the migrate_system_files.py but remove user-specific backups
        user_backup_dirs = ['bryan', 'raysan', 'risan', 'user1']
        for user_dir in user_backup_dirs:
            user_path = os.path.join(backup_dir, user_dir)
            if os.path.exists(user_path):
                print(f"Removing user backup: {user_path}")
                shutil.rmtree(user_path)

def remove_old_logs(root_dir):
    """Remove old rotated log files but keep current ones"""
    logs_dir = os.path.join(root_dir, 'data', 'logs')
    if os.path.exists(logs_dir):
        for file in os.listdir(logs_dir):
            if file.endswith(('.1', '.2', '.3', '.4', '.5')):
                file_path = os.path.join(logs_dir, file)
                print(f"Removing old log: {file_path}")
                os.remove(file_path)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Cleaning up project at: {root_dir}")
    
    print("\n1. Removing __pycache__ directories...")
    remove_pycache_dirs(root_dir)
    
    print("\n2. Removing debug/temporary scripts...")
    remove_debug_scripts(root_dir)
    
    print("\n3. Removing backup files...")
    remove_backup_files(root_dir)
    
    print("\n4. Removing old log files...")
    remove_old_logs(root_dir)
    
    print("\nCleanup completed!")

if __name__ == "__main__":
    main()
