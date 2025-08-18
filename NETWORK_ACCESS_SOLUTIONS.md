# Network Access Issues - Solutions and Workarounds

## Problem Description
Admin users are getting "Access is denied" errors when trying to move approved files to `\\KMTI-NAS\Database\PROJECTS\{team}\{year}` directory due to insufficient network permissions.

## Root Cause
The Windows account running the application doesn't have:
1. **Write permissions** to the `\\KMTI-NAS\Database\PROJECTS\` directory
2. **Create folder permissions** to create team and year subdirectories
3. **Network authentication** to access the NAS server

## Solutions Implemented

### 1. **Enhanced File Movement Service** ✅
- **Fallback mechanism**: Files are moved to `\\KMTI-NAS\Shared\data\approved_files_staging\{team}\{year}` if direct access fails
- **Access testing**: Automatically tests network access before attempting moves
- **Request system**: Creates admin access requests for manual processing when automatic moves fail

### 2. **Admin Access Request System** ✅
- **Request tracking**: Failed moves create JSON request files with all necessary information
- **Manual processing**: Admin can mark files as manually moved
- **Retry mechanism**: Admins can retry automatic moves after fixing permissions

### 3. **Administrative Tools** ✅
- **`process_admin_requests.py`**: Interactive script for managing access requests
- **Access requests panel**: GUI interface in admin panel for managing requests
- **Automated cleanup**: Old completed requests are automatically cleaned up

## Network Access Solutions

### **Option 1: Fix Network Permissions (Recommended)**

#### **For System Administrator:**
1. **Grant full control** to the Windows account running the KMTI application:
   ```
   \\KMTI-NAS\Database\PROJECTS\
   ```

2. **Set permissions using Windows Explorer:**
   - Right-click on `\\KMTI-NAS\Database\PROJECTS\`
   - Select "Properties" → "Security" tab
   - Click "Edit" → "Add"
   - Add the Windows account running the application
   - Grant "Full Control" permissions
   - Check "Apply to subfolders and files"

3. **Alternative: Use network credentials:**
   ```cmd
   net use \\KMTI-NAS /user:domain\username password /persistent:yes
   ```

#### **For Network Administrator:**
1. **Create a service account** with appropriate permissions
2. **Run KMTI application** under this service account
3. **Configure NAS permissions** to allow the service account full access to PROJECTS directory

### **Option 2: Use Fallback Directory (Current Implementation)**

Files are automatically moved to the fallback location:
```
\\KMTI-NAS\Shared\data\approved_files_staging\{team}\{year}\
```

**Admin then manually moves files:**
1. Copy files from staging directory
2. Move to final location: `\\KMTI-NAS\Database\PROJECTS\{team}\{year}\`
3. Mark requests as completed using `process_admin_requests.py`

### **Option 3: Local Processing with Network Sync**

#### **Setup Instructions:**
1. **Create local staging directory:**
   ```
   C:\KMTI_Staging\approved_files\
   ```

2. **Configure batch sync script:**
   ```cmd
   robocopy "C:\KMTI_Staging\approved_files" "\\KMTI-NAS\Database\PROJECTS" /E /MOV /LOG:sync.log
   ```

3. **Schedule sync**: Use Windows Task Scheduler to run sync every 30 minutes

## Immediate Workaround Steps

### **Step 1: Process Current Failed Request**
```cmd
python process_admin_requests.py
```

1. Select option "1" to view pending requests
2. Note the file details and target location
3. Manually copy the file:
   - **From**: `\\KMTI-NAS\Shared\data\uploads\user\filename.ext`
   - **To**: `\\KMTI-NAS\Database\PROJECTS\KUSAKABE\2025\filename.ext`
4. Select option "2" to mark as manually completed
5. Enter the request ID when prompted

### **Step 2: Enable Enhanced Movement Service** ✅
The enhanced service is already enabled and will:
- Test network access before each move attempt
- Use fallback directory if direct access fails
- Create detailed request logs for manual processing

### **Step 3: Monitor Access Requests**
- **Command line**: Run `python process_admin_requests.py` regularly
- **GUI**: Use admin panel → Access Requests tab
- **Automatic**: Set up scheduled task to check and process requests

## Testing Network Access

### **Manual Test:**
```cmd
# Test directory creation
mkdir "\\KMTI-NAS\Database\PROJECTS\TEST_ACCESS_2025"

# If successful, clean up
rmdir "\\KMTI-NAS\Database\PROJECTS\TEST_ACCESS_2025"
```

### **Application Test:**
```python
python debug_approval_workflow.py
```
Look for network access test results in the output.

## Monitoring and Maintenance

### **Daily Tasks:**
1. **Check pending requests**: `python process_admin_requests.py`
2. **Process manual moves**: Move files from staging to final locations
3. **Update request status**: Mark completed requests

### **Weekly Tasks:**
1. **Review access patterns**: Check which teams/users have frequent access issues
2. **Clean up old requests**: Use cleanup option in processing script
3. **Test network connectivity**: Verify all paths are accessible

### **Monthly Tasks:**
1. **Review permissions**: Ensure service account has necessary access
2. **Update documentation**: Note any new access issues or solutions
3. **Performance review**: Check if manual processes can be automated

## Error Messages and Solutions

### **"Access is denied"**
- **Solution**: Fix network permissions or use fallback directory
- **Workaround**: Manual file movement using `process_admin_requests.py`

### **"Path not found"**
- **Solution**: Verify network connection to NAS server
- **Check**: `ping KMTI-NAS` to verify connectivity

### **"Network path not available"**
- **Solution**: Check network connection and NAS server status
- **Verify**: Other network shares are accessible

### **"Insufficient privileges"**
- **Solution**: Run application as administrator or use service account
- **Alternative**: Grant specific permissions to current user account

## Future Enhancements

### **Automatic Permission Management**
- **Service account integration**: Automatically use service account credentials
- **Permission checking**: Pre-validate access before starting approval workflow
- **Smart fallback**: Choose best available location based on permissions

### **Enhanced Monitoring**
- **Dashboard**: Show network access status in admin panel
- **Alerts**: Email notifications for failed moves
- **Metrics**: Track success rates and common failure points

### **Batch Processing**
- **Scheduled moves**: Automatically retry failed moves during off-hours
- **Bulk processing**: Move multiple files at once when access is available
- **Queue management**: Prioritize moves based on file age and importance

## Contact Information

For network access issues:
- **System Administrator**: Configure Windows/NAS permissions
- **Network Administrator**: Verify NAS connectivity and shares
- **Application Support**: Use `process_admin_requests.py` for immediate workarounds

## Summary

The KMTI system now gracefully handles network access issues by:
1. **Testing access** before attempting moves
2. **Using fallback directories** when direct access fails
3. **Creating detailed requests** for manual processing
4. **Providing tools** for admins to manage access issues
5. **Maintaining audit trails** of all file movements

Files will always be approved and users notified, even if the final file placement requires manual intervention.
