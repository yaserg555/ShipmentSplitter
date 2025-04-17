# Building the FBA Shipment Splitter Executable (Windows)

This document outlines the steps to build the standalone `.exe` file for the FBA Shipment Splitter application from the source code using a virtual environment.

## Prerequisites

*   Python 3 installed and added to your system's PATH.
*   Git installed (optional, for cloning the repository).

## Build Steps

1.  **Navigate to the Build Directory:**
    Open your terminal or command prompt and navigate into the specific directory containing the build source code:
    ```bash
    cd fbashipmentsplitbuild_windows
    ```

2.  **Create a Virtual Environment:**
    Create an isolated Python virtual environment named `.venv` within this directory. This keeps the project's dependencies separate from your global Python installation.
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    Activate the newly created environment. The command differs slightly depending on your shell:
    *   **Command Prompt (cmd.exe):**
        ```bash
        .\.venv\Scripts\activate.bat
        ```
    *   **PowerShell:**
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
        *(Note: If you encounter an execution policy error in PowerShell, you might need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first).*
    *   **Git Bash or other bash-like shells:**
        ```bash
        source .venv/Scripts/activate
        ```
    Your terminal prompt should now indicate that the `.venv` environment is active (e.g., `(.venv) C:\path\to\project\fbashipmentsplitbuild_windows>`).

4.  **Install Dependencies:**
    Install the required Python packages listed in `requirements.txt` into the active virtual environment.
    ```bash
    python -m pip install -r requirements.txt
    ```

5.  **Install PyInstaller:**
    Install PyInstaller, the tool used to package the application into an executable.
    ```bash
    python -m pip install pyinstaller
    ```

6.  **Run PyInstaller:**
    Execute PyInstaller to build the application. This command bundles your script (`main.py`), its dependencies (like PyMuPDF), and necessary parts of the Python interpreter into a single executable file.
    *   `--onefile`: Creates a single `.exe` file.
    *   `--windowed`: Prevents a console window from appearing when the GUI application runs. Omit this if it's a command-line application.
    ```bash
    pyinstaller --onefile --windowed main.py
    ```
    PyInstaller will create `build` and `dist` folders, along with a `.spec` file.

7.  **Locate the Executable:**
    The final standalone executable (`main.exe`) will be located inside the `dist` folder.

8.  **Deactivate Virtual Environment (Optional):**
    Once you are finished building, you can deactivate the virtual environment by simply running:
    ```bash
    deactivate
    ```

You can now copy the `main.exe` file from the `dist` folder and run it on other Windows machines without needing Python or the dependencies installed.
