import os
from pathlib import Path

def setup_nas_structure():
    """Create NAS directory structure"""
    nas_base = Path("\\\\KMTI-NAS\\SHARED")
    
    if not nas_base.exists():
        print("❌ Cannot access \\\\KMTI-NAS\\SHARED")
        print("   Make sure the NAS is accessible and mapped correctly")
        return False
    
    # Create data directory
    data_dir = nas_base / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    subdirs = ["documents", "temp", "backups", "logs"]
    for subdir in subdirs:
        (data_dir / subdir).mkdir(exist_ok=True)
    
    print(f"✅ Created NAS structure at {data_dir}")
    print("📁 Structure created:")
    print("   \\\\KMTI-NAS\\SHARED\\data\\")
    print("   ├── documents\\")
    print("   ├── temp\\")
    print("   ├── backups\\")
    print("   └── logs\\")
    
    return True

if __name__ == "__main__":
    setup_nas_structure()