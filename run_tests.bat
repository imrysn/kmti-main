@echo off
REM KMTI Test Suite - Windows Batch Runner
REM =====================================
REM
REM This batch file provides easy access to KMTI testing tools for Windows users.
REM Double-click to run or execute from command prompt.

title KMTI Test Suite

echo.
echo ===============================================
echo    KMTI Data Management System Test Suite
echo ===============================================
echo.

:MENU
echo Please select an option:
echo.
echo   1. Setup Test Environment
echo   2. Validate Test Suite
echo   3. Run Quick Tests (Essential)
echo   4. Run Smoke Tests (Basic Health Check)
echo   5. Run Full Test Suite (Comprehensive)
echo   6. Run Performance Benchmark
echo   7. Analyze Test Results
echo   8. View Testing Documentation
echo   9. Exit
echo.

set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto VALIDATE
if "%choice%"=="3" goto QUICK
if "%choice%"=="4" goto SMOKE
if "%choice%"=="5" goto FULL
if "%choice%"=="6" goto BENCHMARK
if "%choice%"=="7" goto ANALYZE
if "%choice%"=="8" goto DOCS
if "%choice%"=="9" goto EXIT

echo Invalid choice. Please try again.
echo.
goto MENU

:SETUP
echo.
echo ===============================================
echo Setting up test environment...
echo ===============================================
echo.
python setup_test_environment.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup failed. Please check the error messages above.
    pause
    goto MENU
)
echo.
echo Setup completed successfully!
pause
goto MENU

:VALIDATE
echo.
echo ===============================================
echo Validating test suite...
echo ===============================================
echo.
python validate_test_suite.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Validation found issues. Please review the messages above.
    pause
    goto MENU
)
echo.
echo Validation completed successfully!
pause
goto MENU

:QUICK
echo.
echo ===============================================
echo Running Quick Tests (Essential functionality)...
echo ===============================================
echo.
python run_kmti_tests.py --quick
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests failed. Check test_data/test_report.txt for details.
    pause
    goto MENU
)
echo.
echo Quick tests completed! Check test_data/test_report.txt for results.
pause
goto MENU

:SMOKE
echo.
echo ===============================================
echo Running Smoke Tests (Basic health check)...
echo ===============================================
echo.
python run_kmti_tests.py --smoke
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests failed. Check test_data/test_report.txt for details.
    pause
    goto MENU
)
echo.
echo Smoke tests completed! System health looks good.
pause
goto MENU

:FULL
echo.
echo ===============================================
echo Running Full Test Suite (This may take 15-30 minutes)...
echo ===============================================
echo.
echo WARNING: This will run all comprehensive tests.
echo This may take a significant amount of time.
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

python run_kmti_tests.py --verbose
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests failed. Check test_data/test_report.txt for details.
    pause
    goto MENU
)
echo.
echo Full test suite completed! Check test_data/test_report.txt for results.
pause
goto MENU

:BENCHMARK
echo.
echo ===============================================
echo Running Performance Benchmark...
echo ===============================================
echo.
python benchmark_kmti_performance.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Benchmark failed. Please check the error messages above.
    pause
    goto MENU
)
echo.
echo Performance benchmark completed! Check benchmark_report.md for results.
pause
goto MENU

:ANALYZE
echo.
echo ===============================================
echo Analyzing Test Results...
echo ===============================================
echo.
if not exist "test_data\test_report.txt" (
    echo No test results found. Please run tests first.
    pause
    goto MENU
)

python analyze_test_results.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Analysis failed. Please check the error messages above.
    pause
    goto MENU
)
echo.
echo Results analysis completed! Check test_analysis_report.md for insights.
pause
goto MENU

:DOCS
echo.
echo ===============================================
echo Opening Testing Documentation...
echo ===============================================
echo.
echo Available documentation files:
echo.
echo   - README_TESTING.md        (Testing suite overview)
echo   - TESTING_GUIDE.md         (Detailed testing guide)
echo   - test_data\test_report.txt (Latest test results)
echo   - benchmark_report.md       (Performance results)
echo.
echo Opening README_TESTING.md in default text editor...
echo.

if exist "README_TESTING.md" (
    start "" "README_TESTING.md"
) else (
    echo README_TESTING.md not found. Please ensure you're running from the correct directory.
)

pause
goto MENU

:EXIT
echo.
echo ===============================================
echo Thank you for using KMTI Test Suite!
echo ===============================================
echo.
echo For more information, check:
echo   - README_TESTING.md (Testing overview)
echo   - TESTING_GUIDE.md (Detailed guide)
echo.
echo Have a great day!
pause
exit /b 0
