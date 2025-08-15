"""
KMTI File Approval System - Status Constants
Clean 3-stage workflow implementation
"""

class FileApprovalStatus:
    """Clean status constants for 3-stage approval workflow"""
    
    # Stage 0: File uploaded but not submitted
    MY_FILES = "my_files"
    
    # Stage 1: Submitted for Team Leader review  
    PENDING_TEAM_LEADER = "pending_team_leader"
    
    # Stage 2: Team Leader approved, now with Admin
    PENDING_ADMIN = "pending_admin"
    
    # Stage 3: Final approval
    APPROVED = "approved"
    
    # Rejection states
    REJECTED_TEAM_LEADER = "rejected_team_leader" 
    REJECTED_ADMIN = "rejected_admin"
    
    # Other states
    WITHDRAWN = "withdrawn"
    CHANGES_REQUESTED = "changes_requested"

    @classmethod
    def get_all_statuses(cls):
        """Get all available statuses"""
        return [
            cls.MY_FILES, cls.PENDING_TEAM_LEADER, cls.PENDING_ADMIN,
            cls.APPROVED, cls.REJECTED_TEAM_LEADER, cls.REJECTED_ADMIN, 
            cls.WITHDRAWN, cls.CHANGES_REQUESTED
        ]

# Legacy compatibility - for old code that imports ApprovalStatus
ApprovalStatus = FileApprovalStatus
