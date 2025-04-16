@echo off
echo PDF Splitter - Batch Processing
echo ==============================
echo.

if "%~1"=="" (
    echo Usage: process_all_shipments.bat [directory_path]
    echo.
    echo Example: process_all_shipments.bat "E:\Developing\ShipmentSplitter\test 2"
    exit /b 1
)

echo Processing files in: %1
echo Output folders will be created as subfolders in this directory
echo.

python E:\Developing\ShipmentSplitter\process_all.py "%~1"

echo.
echo Process completed.
pause
