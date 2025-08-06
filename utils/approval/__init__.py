"""File approval system package for handling file upload approvals and management.

This package provides functionality for managing file approvals, including:
- File upload to approval queue
- Approval/rejection of files
- Metadata tracking
- Comment management
"""

from .file_approver import (
    load_metadata,
    save_metadata,
    add_comment,
    approve_file,
    reject_file,
    get_pending_files,
    APPROVAL_QUEUE,
    APPROVED_DB,
    METADATA_FILE
)

__all__ = [
    'load_metadata',
    'save_metadata',
    'add_comment',
    'approve_file',
    'reject_file',
    'get_pending_files',
    'APPROVAL_QUEUE',
    'APPROVED_DB',
    'METADATA_FILE'
]
