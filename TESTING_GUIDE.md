# KMTI Data Management System - Test Suite Documentation

## 🧪 Comprehensive Testing Framework

This test suite provides complete functionality testing for the KMTI Data Management System, covering all user roles, features, and edge cases.

## 📁 Test Files

- **`kmti_comprehensive_test.py`** - Main comprehensive test suite with 11 test categories
- **`run_kmti_tests.py`** - Simplified test runner with preset configurations
- **`TESTING_GUIDE.md`** - This documentation file

## 🚀 Quick Start

### Simple Test Execution

```bash
# Run all tests (comprehensive)
python run_kmti_tests.py

# Quick essential tests (~5 minutes)
python run_kmti_tests.py --quick

# Basic smoke tests (~2 minutes)  
python run_kmti_tests.py --smoke

# Test specific component
python run_kmti_tests.py --component auth
```

### Advanced Test Options

```bash
# Full comprehensive test with verbose output
python kmti_comprehensive_test.py --verbose

# Test specific categories
python kmti_comprehensive_test.py --categories auth_tests file_management_tests

# Custom output directory
python kmti_comprehensive_test.py --output custom_test_results
```

## 📋 Test Categories

### 1. 🔐 Authentication Tests (`auth_tests`)
**What it tests:**
- Admin, user, and team leader login functionality
- Password hashing and security validation
- Enhanced authentication with security features
- Session management and restoration
- Input sanitization and security measures

**Key Test Cases:**
- Valid login attempts for all roles
- Invalid credential rejection
- Password strength validation
- Session token generation and validation
- Security input sanitization

### 2. 📄 File Management Tests (`file_management_tests`)
**What it tests:**
- File upload simulation and validation
- File metadata management (descriptions, tags)
- File security validation and sanitization
- File type detection and size calculations
- System file filtering and protection

**Key Test Cases:**
- File upload workflow simulation
- Metadata persistence and loading
- Malicious filename rejection
- File extension validation
- File size calculation accuracy

### 3. 🔄 Approval Workflow Tests (`approval_workflow_tests`)
**What it tests:**
- Complete file submission workflow
- Team leader approval process
- Admin final approval process
- File rejection workflow
- Notification system for status updates

**Key Test Cases:**
- File submission structure validation
- Status transitions (pending_team_leader → pending_admin → approved)
- Approval history tracking
- Notification generation and delivery
- File archiving after approval/rejection

### 4. 👨‍💼 Admin Panel Tests (`admin_panel_tests`)
**What it tests:**
- User management operations (create, modify, delete)
- Activity logging and audit trails
- System statistics calculation
- File approval management interface
- Team management functionality

**Key Test Cases:**
- User CRUD operations
- Activity log generation
- Statistical data accuracy
- File queue management
- Team assignment operations

### 5. 👥 Team Leader Tests (`team_leader_tests`)
**What it tests:**
- Team-specific file visibility
- Team leader approval authority
- Team leader rejection functionality
- Team-based dashboard statistics

**Key Test Cases:**
- File filtering by team membership
- Team leader approval workflow
- Rejection authority validation
- Team statistics calculation

### 6. 👤 User Panel Tests (`user_panel_tests`)
**What it tests:**
- User file listing and visibility
- Profile management functionality
- Notification system display
- File submission process

**Key Test Cases:**
- File listing with system file exclusion
- Profile update operations
- Notification loading and management
- File submission workflow

### 7. 🔍 Data Integrity Tests (`data_integrity_tests`)
**What it tests:**
- User data consistency across files
- File metadata integrity
- Approval status consistency
- Database backup and recovery

**Key Test Cases:**
- Cross-file data consistency validation
- Metadata-file relationship integrity
- User vs. global approval status matching
- Backup/restore functionality

### 8. ⚡ Performance Tests (`performance_tests`)
**What it tests:**
- Large file handling efficiency
- Concurrent user operations
- Database query performance
- Memory usage optimization

**Key Test Cases:**
- Large file processing times
- Multi-user concurrent operations
- Query performance with large datasets
- Memory usage and cleanup

### 9. 🔒 Security Tests (`security_tests`)
**What it tests:**
- Path traversal attack protection
- File upload security measures
- Input sanitization and validation
- Authentication security features
- Session security measures

**Key Test Cases:**
- Malicious path blocking
- File extension security validation
- XSS and SQL injection protection
- Password strength enforcement
- Session token security

### 10. 🚨 Error Handling Tests (`error_handling_tests`)
**What it tests:**
- File system error recovery
- Database corruption handling
- Network failure recovery
- Validation error management
- Graceful degradation

**Key Test Cases:**
- File not found handling
- JSON corruption recovery
- Network path fallback
- Input validation error messages
- Service failure graceful handling

### 11. 🔗 Integration Tests (`integration_tests`)
**What it tests:**
- Complete end-to-end user workflows
- System startup and shutdown procedures
- Cross-component communication

**Key Test Cases:**
- Full user registration → file upload → approval → notification workflow
- System initialization sequence
- Component-to-component data flow

## 📊 Test Results and Reporting

### Console Output
Real-time progress with colored status indicators:
- ✅ Passed tests
- ❌ Failed tests  
- 💥 Error tests
- 📁 Test category summaries

### Generated Files
- **`kmti_test_results.log`** - Detailed test execution log
- **`test_data/test_report.txt`** - Comprehensive test report
- **`test_data/`** - Test data directory with mock files and databases

### Report Sections
1. **Executive Summary** - Pass/fail statistics and timing
2. **Category Breakdown** - Results by test category
3. **Detailed Results** - Individual test case results
4. **Performance Metrics** - Timing and resource usage data

## 🔧 Test Configuration

### Environment Setup
The test suite automatically creates:
- Mock user database with test accounts
- Sample file uploads and metadata
- Approval workflow test data
- Network path simulation
- System configuration files

### Test Users
Pre-configured test users for different roles:
- **test_admin** (ADMIN role) - Full system access
- **test_teamlead** (TEAM_LEADER role) - Engineering team leader
- **test_user** (USER role) - Engineering team member
- **test_user2** (USER role) - Design team member

### Test Files
Sample files for upload and workflow testing:
- PDF documents
- DWG design files
- PNG images
- ZIP archives
- Large files for performance testing

## 📈 Success Criteria

### Individual Tests
- **Pass**: Test meets expected behavior
- **Fail**: Test doesn't meet expected behavior  
- **Error**: Test encounters unexpected exception

### Category Success
- **✅ Good**: 90%+ tests passing
- **⚠️ Warning**: 75-89% tests passing
- **❌ Critical**: <75% tests passing

### Overall System Health
- **Healthy**: All critical categories passing
- **Degraded**: Some non-critical failures
- **Critical**: Core functionality failures

## 🛠️ Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root directory
cd /path/to/kmti-main
python run_kmti_tests.py
```

#### Permission Errors
```bash
# Run with appropriate permissions
# On Windows (if needed):
python run_kmti_tests.py

# On Linux/Mac:
sudo python run_kmti_tests.py  # Only if necessary
```

#### Network Path Issues
The tests use mock network paths - they don't require actual network connectivity to `\\KMTI-NAS\`.

#### Memory Issues
```bash
# For systems with limited memory, use smaller test sets:
python run_kmti_tests.py --quick
```

### Test Failures

#### Authentication Test Failures
- Check that test users file is properly created
- Verify password hashing is working
- Ensure mock path configuration is correct

#### File Management Test Failures  
- Verify test data directory permissions
- Check file creation and cleanup
- Ensure sufficient disk space

#### Integration Test Failures
- These are complex workflows - check detailed logs
- Verify all components are properly mocked
- Check for dependency issues between test components

## 🎯 Best Practices

### Before Running Tests
1. Ensure system is in clean state
2. Close any running KMTI applications
3. Have sufficient disk space (at least 100MB)
4. Run from project root directory

### During Testing
1. Don't interrupt tests unless necessary
2. Monitor console output for progress
3. Note any warning messages
4. Let long-running tests complete

### After Testing
1. Review the generated test report
2. Check detailed logs for any issues
3. Clean up test data if desired
4. Document any consistent failures

## 🚀 Advanced Usage

### Custom Test Development
To add new tests, extend the appropriate test class:

```python
class CustomTests(BaseTestClass):
    def test_custom_functionality(self) -> Tuple[bool, str]:
        try:
            # Your test logic here
            result = some_function_to_test()
            if result == expected_value:
                return True, "Custom test passed"
            else:
                return False, "Custom test failed"
        except Exception as e:
            return False, f"Custom test error: {str(e)}"
```

### Continuous Integration
For CI/CD pipelines:

```bash
# Exit with proper codes for CI systems
python run_kmti_tests.py --quick
echo "Exit code: $?"

# Generate machine-readable results
python kmti_comprehensive_test.py --output ci_results
```

### Performance Monitoring
Track test execution times:

```bash
# Run with timing information
time python run_kmti_tests.py --performance --verbose
```

## 📚 Additional Resources

- **Main README**: `README_updated.md` - System documentation
- **System Status**: `SYSTEM_STATUS.md` - Current system state
- **Cleanup Report**: `CLEANUP_REPORT.md` - Recent cleanup activities
- **Source Code**: Explore the `utils/`, `admin/`, `user/`, and `services/` directories

## 🤝 Support

If you encounter issues with the test suite:

1. **Check the detailed logs** - Most issues have clear error messages
2. **Review this documentation** - Common solutions are documented here  
3. **Verify system requirements** - Ensure Python 3.8+ and required dependencies
4. **Clean test environment** - Delete `test_data/` directory and re-run
5. **Contact system maintainer** - With test report and logs

---

**Happy Testing! 🧪✨**

The KMTI test suite ensures your system is working correctly and helps maintain code quality as the system evolves.
