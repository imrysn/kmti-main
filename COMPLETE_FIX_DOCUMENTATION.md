# KMTI File Approval System - Complete Fix Documentation

## Issues Addressed

### 1. **Files not displaying in TLPanel and Admin Panel**
**Root Cause**: Path inconsistencies and status mismatches between services
**Solution**: 
- Updated all services to use centralized path configuration
- Fixed status workflow from "pending" to proper "pending_team_leader" → "pending_admin"
- Ensured TL and Admin panels read from the same network data source

### 2. **File Movement to Project Directory**
**Root Cause**: Files were staying in upload directory after approval
**Solution**: 
- Created `FileMovementService` that moves approved files to `\\KMTI-NAS\Database\PROJECTS\{team_tag}\{YYYY}`
- Integrated file movement into admin approval workflow
- Added metadata tracking for moved files

## New Files Created

### 1. **`services/file_movement_service.py`**
- Handles moving approved files to project directories
- Creates metadata files for tracking
- Manages project directory structure by team and year

### 2. **`debug_approval_workflow.py`**
- Comprehensive debugging script
- Checks network connectivity, queue status, and service functionality
- Helps identify workflow issues

### 3. **`fix_approval_statuses.py`**
- Fixes inconsistent file statuses
- Synchronizes data between global queue and user files
- Creates missing directories

## Files Modified

### 1. **Path Configuration Updates**
- `utils/path_config.py` - Enhanced with better logging
- `main.py` - Uses centralized paths
- `user/user_panel.py` - Network paths for user folders

### 2. **Service Updates**
- `services/approval_service.py` - Integrated file movement on approval
- `admin/components/team_leader_service.py` - Uses network paths
- `user/services/approval_file_service.py` - Network paths for approvals

### 3. **Data Migration**
- `migrate_to_network_storage.py` - Safely migrates existing data
- `NETWORK_MIGRATION_SUMMARY.md` - Complete migration documentation

## New Workflow

### **File Submission Process**
1. **User uploads file** → File stored in `\\KMTI-NAS\Shared\data\uploads\{username}\`
2. **User submits for approval** → Status: `pending_team_leader`
3. **Team Leader reviews** → Status: `pending_admin` (if approved)
4. **Admin reviews** → File moved to `\\KMTI-NAS\Database\PROJECTS\{team_tag}\{YYYY}\` (if approved)

### **Directory Structure**
```
\\KMTI-NAS\Shared\data\                    # Shared application data
├── approvals/
│   └── file_approvals.json               # Global approval queue
├── uploads/
│   └── {username}/                        # User upload directories
├── user_approvals/
│   └── {username}/                        # User approval status data
└── users.json                            # User configuration

\\KMTI-NAS\Database\PROJECTS\              # Final approved files
├── {TEAM_TAG}/
│   └── {YYYY}/
│       ├── approved_file.ext              # Moved approved file
│       └── approved_file.metadata.json   # File metadata
```

## Setup Instructions

### **For New Installations**
1. Ensure network access to `\\KMTI-NAS\Shared\data\` and `\\KMTI-NAS\Database\PROJECTS\`
2. Run the application - directories will be created automatically
3. Create users with proper `team_tags` in users.json

### **For Existing Installations** 

#### **Step 1: Backup Data**
```bash
# Create backup of current data directory
xcopy data backup\pre_migration\ /E /I
```

#### **Step 2: Run Migration**
```bash
python migrate_to_network_storage.py
```

#### **Step 3: Fix Status Issues**
```bash
python fix_approval_statuses.py
```

#### **Step 4: Verify System**
```bash
python debug_approval_workflow.py
```

## Testing Workflow

### **1. Test User Upload**
1. Login as a regular user
2. Upload a test file
3. Submit file for approval
4. Verify status shows as "pending_team_leader"

### **2. Test Team Leader Approval**
1. Login as team leader for the user's team
2. Verify file appears in TL Panel
3. Approve the file
4. Verify status changes to "pending_admin"

### **3. Test Admin Approval**
1. Login as admin
2. Verify file appears in Admin Panel
3. Approve the file
4. Verify file is moved to project directory: `\\KMTI-NAS\Database\PROJECTS\{team_tag}\{YYYY}\`

## Configuration Requirements

### **users.json Format**
```json
{
  "user@example.com": {
    "username": "testuser",
    "role": "USER",
    "team_tags": ["AGCC"],
    "password": "hashed_password"
  },
  "teamlead@example.com": {
    "username": "teamlead",
    "role": "TEAM_LEADER",
    "team_tags": ["AGCC"],
    "password": "hashed_password"
  },
  "admin@example.com": {
    "username": "admin",
    "role": "ADMIN",
    "team_tags": ["ALL"],
    "password": "hashed_password"
  }
}
```

### **Required Network Permissions**
- **Read/Write access** to `\\KMTI-NAS\Shared\data\`
- **Read/Write access** to `\\KMTI-NAS\Database\PROJECTS\`
- **Network connectivity** between application server and NAS

## Troubleshooting

### **Files not showing in TL/Admin panels**
1. Run `debug_approval_workflow.py` to check system status
2. Verify network connectivity to shared directories
3. Check that users have correct `team_tags` in users.json
4. Run `fix_approval_statuses.py` to fix status inconsistencies

### **File movement failures**
1. Check permissions on `\\KMTI-NAS\Database\PROJECTS\`
2. Verify team directories exist or can be created
3. Check disk space on target directory
4. Review logs for specific error messages

### **Path-related errors**
1. Ensure `utils/path_config.py` is imported correctly in all services
2. Verify network paths are accessible
3. Check that `DATA_PATHS.is_network_available()` returns True

### **Performance issues**
1. Check network bandwidth and latency
2. Consider local caching for frequently accessed data
3. Monitor disk I/O on network storage
4. Optimize file indexing and search operations

## Security Considerations

### **Network Security**
- Ensure NAS access is restricted to authorized users only
- Use secure network protocols (SMB3.0+ with encryption)
- Implement proper authentication and access controls
- Regular security audits of network access logs

### **Data Protection**
- Regular backups of both `\\KMTI-NAS\Shared\data\` and project directories
- Implement version control for critical configuration files
- Monitor file access and modifications
- Secure file metadata to prevent tampering

## Monitoring and Maintenance

### **Regular Checks**
- Run `debug_approval_workflow.py` weekly to verify system health
- Monitor disk usage on network directories
- Check for orphaned files or broken references
- Verify backup procedures are working correctly

### **Performance Monitoring**
- Track file upload/download speeds
- Monitor approval workflow completion times
- Check for network connectivity issues
- Review application logs for errors or warnings

## Future Enhancements

### **Potential Improvements**
1. **Automated Testing**: Create comprehensive test suite for workflow validation
2. **Dashboard Analytics**: Add reporting on approval times, file volumes, team performance
3. **Notification System**: Email/SMS notifications for pending approvals
4. **File Versioning**: Support for file revisions and version control
5. **Bulk Operations**: Support for bulk approval/rejection of files
6. **Advanced Search**: Full-text search capabilities for approved files
7. **Integration APIs**: REST APIs for external system integration

### **Scalability Considerations**
- Implement database backend for large-scale deployments
- Add load balancing for multiple application servers
- Consider cloud storage integration for hybrid deployments
- Implement distributed file caching for improved performance

## Conclusion

The KMTI File Approval System has been successfully updated to address the display and file movement issues. The key improvements include:

- **Centralized path management** for consistent data access
- **Proper workflow status handling** ensuring files flow correctly through TL → Admin approval
- **Automated file movement** to project directories upon final approval
- **Comprehensive debugging and fix tools** for system maintenance
- **Robust error handling and logging** for troubleshooting

The system now provides a complete end-to-end file approval workflow with proper separation of concerns and reliable data management.
