"""
Script de Compilación a Ejecutable
==================================

Este script automatiza la creación de un ejecutable (.exe) del servidor HTTP proxy
usando PyInstaller con configuración optimizada para entornos Windows.

Características del ejecutable generado:
- ✅ Ejecutable independiente (no requiere Python instalado)
- ✅ Sin ventana de consola (background service)
- ✅ Todas las dependencias incluidas
- ✅ Icono personalizado (si está disponible)
- ✅ Información de versión integrada
- ✅ Optimizado para tamaño y velocidad

Autor: Raul Mauricio Uñate Castro
Fecha: 2026-01-15
"""

import subprocess
import sys
import os
from pathlib import Path
import venv
import shutil

# ============================================================================
# CONFIGURACIÓN DE COMPILACIÓN
# ============================================================================

# Configuración principal del ejecutable
CONFIG = {
    "script_name": "server.py",
    "exe_name": "HttpProxyServer",
    "version": "2.0.0",
    "description": "HTTP Proxy Server - Servidor proxy con sesiones persistentes",
    "company": "Open Source",
    "copyright": "© 2026 Raul Mauricio Uñate Castro",
    "icon_file": "icon.ico",
    "venv_name": "tmp_venv",
    "hidden_imports": [
        "uvicorn.workers",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "httptools",
        "websockets",
        "pydantic.v1",
        "email_validator"
    ]
}

# Rutas del entorno virtual
VENV_PATH = Path(CONFIG["venv_name"])
if sys.platform == "win32":
    VENV_PYTHON = VENV_PATH / "Scripts" / "python.exe"
    VENV_PIP = VENV_PATH / "Scripts" / "pip.exe"
    VENV_PYINSTALLER = VENV_PATH / "Scripts" / "pyinstaller.exe"
else:
    VENV_PYTHON = VENV_PATH / "bin" / "python"
    VENV_PIP = VENV_PATH / "bin" / "pip"
    VENV_PYINSTALLER = VENV_PATH / "bin" / "pyinstaller"

def setup_virtual_environment() -> bool:
    """
    Create and configure a clean virtual environment for compilation.

    Returns
    -------
    bool
        True if the virtual environment was set up successfully, False otherwise.
    """
    print("🔧 Setting up virtual environment for compilation...")

    try:
        # Remove existing virtual environment if present
        if VENV_PATH.exists():
            print("🗑️  Removing previous virtual environment...")
            shutil.rmtree(VENV_PATH)

        # Create a new virtual environment with pip
        print(f"🆕 Creating virtual environment: {VENV_PATH}")
        venv.create(VENV_PATH, with_pip=True)

        # Verify that the virtual environment was created successfully
        if not VENV_PYTHON.exists():
            print("❌ Error: Could not create the virtual environment")
            return False

        print("✅ Virtual environment created successfully")
        print(f"📍 Virtual environment Python: {VENV_PYTHON}")

        return True

    except Exception as e:

        error_msg = f"❌ Error setting up virtual environment: {e}"
        print(error_msg)
        return False

def install_build_dependencies() -> bool:
    """
    Install build dependencies in the virtual environment.

    Installs required build packages and project dependencies from requirements.txt
    into the isolated virtual environment.

    Returns
    -------
    bool
        True if all dependencies were installed successfully, False otherwise.
    """
    print("📦 Installing build dependencies in virtual environment...")

    # List of essential build packages
    build_packages = [
        "pyinstaller",
        "setuptools",
        "wheel"
    ]

    # Install project dependencies from requirements.txt if present
    if Path("requirements.txt").exists():
        print("📋 Installing project dependencies...")
        try:
            result = subprocess.run(
                [str(VENV_PIP), "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Project dependencies installed")
        except subprocess.CalledProcessError as e:
            error_msg = "❌ Error installing project dependencies:\n" + e.stderr
            print(error_msg)
            return False

    # Install each build package individually
    for package in build_packages:
        print(f"🔧 Installing {package}...")
        try:
            result = subprocess.run(
                [str(VENV_PIP), "install", package],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Error installing {package}:\n{e.stderr}"
            print(error_msg)
            return False

    # Verify PyInstaller installation
    try:
        result = subprocess.run(
            [str(VENV_PYTHON), "-c", "import PyInstaller; print(PyInstaller.__version__)"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f"✅ PyInstaller {version} is ready in the virtual environment")
        return True
    except subprocess.CalledProcessError:
        error_msg = "❌ Error: PyInstaller was not installed correctly"
        print(error_msg)
        return False

def check_dependencies() -> bool:
    """
    Verify the virtual environment and required dependencies.

    Checks if the virtual environment and PyInstaller are present. If not, it sets up
    the environment and installs necessary build dependencies.

    Returns
    -------
    bool
        True if all dependencies are present or installed successfully, False otherwise.
    """
    print("🔍 Checking virtual environment and dependencies...")

    # Check if the virtual environment's Python executable exists
    if not VENV_PYTHON.exists():
        print("❌ Virtual environment not found. Setting up...")
        if not setup_virtual_environment():
            return False
        if not install_build_dependencies():
            return False
    else:
        print(f"✅ Virtual environment found: {VENV_PATH}")

        # Check if PyInstaller is available in the virtual environment
        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "-c", "import PyInstaller; print(PyInstaller.__version__)"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ PyInstaller {version} is available")
            else:
                print("❌ PyInstaller not found in virtual environment. Installing dependencies...")
                if not install_build_dependencies():
                    return False
        except Exception as e:
            error_msg = f"❌ Error checking PyInstaller: {e}"
            print(error_msg)
            return False

    return True

def create_version_file() -> bool:
    """
    Create the version information file for the executable.

    Writes a version_info.txt file containing metadata for the generated executable.
    The file includes version, company, description, and copyright.

    Returns
    -------
    bool
        True if the version file was created successfully, False otherwise.
    """
    print("📝 Creating version information file...")

    # Format version string for the version resource
    version_parts = CONFIG["version"].replace(".", ", ")

    version_content = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_parts}, 0),
    prodvers=({version_parts}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{CONFIG["company"]}'),
          StringStruct('FileDescription', '{CONFIG["description"]}'),
          StringStruct('FileVersion', '{CONFIG["version"]}'),
          StringStruct('InternalName', '{CONFIG["exe_name"]}'),
          StringStruct('LegalCopyright', '{CONFIG["copyright"]}'),
          StringStruct('OriginalFilename', '{CONFIG["exe_name"]}.exe'),
          StringStruct('ProductName', 'HTTP Proxy Server'),
          StringStruct('ProductVersion', '{CONFIG["version"]}')
        ]
      )
    ]),
    VarFileInfo([
      VarStruct('Translation', [1033, 1200])
    ])
  ]
)'''

    try:
        # Write the version information to a file
        with open("version_info.txt", "w", encoding="utf-8") as f:
            f.write(version_content)
        print("✅ Version file created: version_info.txt")
        return True
    except Exception as e:
        error_msg = f"❌ Error creating version file: {e}"
        print(error_msg)
        return False

def create_pyinstaller_spec() -> str | None:
    """
    Create a custom .spec file for PyInstaller with advanced configuration.

    Returns
    -------
    str or None
        The name of the created spec file, or None if an error occurred.
    """
    print("⚙️  Creating PyInstaller specification...")

    # Determine if the icon file exists
    icon_path = "None"
    if os.path.exists(CONFIG["icon_file"]):
        icon_path = f"'{CONFIG['icon_file']}'"
        print(f"✅ Icon found: {CONFIG['icon_file']}")
    else:
        print("⚠️  Icon not found, using default icon")

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

# Auto-generated configuration by build_exe.py
# HTTP Proxy Server - PyInstaller Specification

a = Analysis(
    ['{CONFIG["script_name"]}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports={CONFIG["hidden_imports"]},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'pytest',
        'unittest',
        'doctest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter unnecessary files to reduce size
a.binaries = [x for x in a.binaries if not x[0].startswith('api-')]
a.datas = [x for x in a.datas if not x[0].startswith('tcl')]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{CONFIG["exe_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon={icon_path}
)'''

    spec_filename = f"{CONFIG['exe_name']}.spec"

    try:
        with open(spec_filename, "w", encoding="utf-8") as f:
            f.write(spec_content)
        print(f"✅ Spec file created: {spec_filename}")
        return spec_filename
    except Exception as e:
        error_msg = f"❌ Error creating spec file: {e}"
        print(error_msg)
        return None

def build_executable() -> bool:
    """
    Build the executable using PyInstaller in the virtual environment.

    This function creates a custom PyInstaller spec file, then runs PyInstaller
    from the virtual environment to generate the standalone executable.

    Returns
    -------
    bool
        True if the build was successful, False otherwise.
    """
    print("\n🔨 Starting build with virtual environment...")

    # Create a custom spec file for PyInstaller
    spec_file = create_pyinstaller_spec()
    if not spec_file:
        return False

    # Prepare the PyInstaller command using the virtual environment
    cmd = [
        str(VENV_PYINSTALLER),
        "--clean",  # Clean cache
        "--noconfirm",  # Do not prompt for confirmations
        spec_file
    ]

    print(f"📋 Running: {' '.join(cmd)}")
    print(f"🐍 Using Python: {VENV_PYTHON}")

    try:
        # Run PyInstaller as a subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            print("✅ Build completed successfully!")

            # Check if the executable was created
            exe_path = Path("dist") / f"{CONFIG['exe_name']}.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 Executable created: {exe_path}")
                print(f"📏 Size: {size_mb:.1f} MB")
                print(f"🎯 Location: {exe_path.absolute()}")
                return True
            else:
                print("❌ Error: Executable not found in the dist/ folder")
                return False
        else:
            print("❌ Error during build:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        error_msg = f"❌ Error running PyInstaller: {e}"
        print(error_msg)
        return False

def cleanup_build_files() -> None:
    """
    Remove temporary build files and directories.

    This function deletes build artifacts such as the build directory,
    __pycache__, the PyInstaller spec file, and the version info file.

    Returns
    -------
    None
        This function does not return a value.
    """
    print("\n🧹 Cleaning up temporary build files...")

    # List of files and directories to remove after build
    cleanup_items = [
        "build",
        "__pycache__",
        f"{CONFIG['exe_name']}.spec",
        "version_info.txt"
    ]

    for item in cleanup_items:
        try:
            if os.path.isdir(item):
                shutil.rmtree(item)
                print(f"🗑️  Directory removed: {item}")
            elif os.path.isfile(item):
                os.remove(item)
                print(f"🗑️  File removed: {item}")
        except Exception as e:
            error_msg = f"⚠️  Could not remove {item}: {e}"
            print(error_msg)

def cleanup_virtual_environment() -> None:
    """
    Remove the temporary virtual environment used for compilation.

    This function deletes the virtual environment directory if it exists.
    It is typically called after a successful build to free up disk space.

    Returns
    -------
    None
        This function does not return a value.
    """
    try:
        # Remove the virtual environment directory if it exists
        if VENV_PATH.exists():
            print(f"🗑️  Removing temporary virtual environment: {VENV_PATH}")
            shutil.rmtree(VENV_PATH)
            print("✅ Temporary virtual environment removed")
        else:
            print("ℹ️  No virtual environment to remove")
    except KeyboardInterrupt:
        print("\n⏹️  Keeping virtual environment")
    except Exception as e:
        error_msg = f"⚠️  Error during cleanup: {e}"
        print(error_msg)

def create_run_script() -> bool:
    """
    Create a batch script to run the server executable.

    The script sets up the environment, creates a logs directory if needed,
    and runs the generated executable.

    Returns
    -------
    bool
        True if the script was created successfully, False otherwise.
    """
    print("📝 Creating run script...")

    # Batch script content for running the server
    run_script = f'''@echo off
title HTTP Proxy Server v{CONFIG["version"]}
echo.
echo ==========================================
echo   HTTP Proxy Server v{CONFIG["version"]}
echo   Starting proxy server...
echo ==========================================
echo.

REM Set environment variables (optional)
REM set SERVER_HOST=0.0.0.0
REM set SERVER_PORT=5003
REM set LOG_LEVEL=info

REM Create logs directory if it does not exist
if not exist "logs" mkdir logs

REM Run the server executable
".\\{CONFIG["exe_name"]}.exe"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error running the server ^(Code: %ERRORLEVEL%^)
    echo    Check if another process is using port 5003
    echo.
) else (
    echo.
    echo ✅ Server closed successfully
)

echo.
echo Press any key to close...
pause >nul
'''

    try:
        # Write the batch script to file
        with open("run_server.bat", "w", encoding="utf-8") as f:
            f.write(run_script)
        print("✅ Run script created: run_server.bat")
        return True
    except Exception as e:
        error_msg = f"❌ Error creating run script: {e}"
        print(error_msg)
        return False

def main() -> bool:
    """
    Run the main build process for the HTTP Proxy Server executable.

    This function orchestrates the compilation process, including environment
    setup, dependency checks, version file creation, executable build, run script
    creation, and cleanup.

    Returns
    -------
    bool
        True if the build process completed successfully, False otherwise.
    """
    print("=" * 80)
    print("🚀 HTTP PROXY SERVER - EXECUTABLE BUILDER")
    print("=" * 80)
    print("📋 Configuration:")
    print(f"   • Source script: {CONFIG['script_name']}")
    print(f"   • Executable name: {CONFIG['exe_name']}.exe")
    print(f"   • Version: {CONFIG['version']}")
    print(f"   • Virtual environment: {CONFIG['venv_name']}")
    print("   • Console: Hidden (background service)")
    print("=" * 80)

    # Check if the main script exists
    if not os.path.exists(CONFIG["script_name"]):
        print(f"❌ Error: File {CONFIG['script_name']} not found")
        print(f"   Verify the file exists at: {os.path.abspath(CONFIG['script_name'])}")
        return False

    try:
        # 1. Set up virtual environment and check dependencies
        if not check_dependencies():
            print("❌ Error setting up the build environment")
            return False

        # 2. Create version file
        if not create_version_file():
            print("❌ Error creating version file")
            return False

        # 3. Build executable
        if build_executable():
            # 4. Create run script
            create_run_script()

            # 5. Clean up temporary build files
            cleanup_build_files()

            print("\n" + "=" * 80)
            print("🎉 BUILD SUCCESSFUL!")
            print("=" * 80)
            print(f"📦 Executable ready: dist\\{CONFIG['exe_name']}.exe")
            print("🎯 Features:")
            print("   • No visible console")
            print("   • Standalone (no Python required)")
            print("   • All dependencies included")
            print("   • Optimized for Windows")
            print("   • Built with a clean virtual environment")
            print("\n💡 To run:")
            print("   1. Go to the 'dist' folder")
            print(f"   2. Run '{CONFIG['exe_name']}.exe'")
            print("   3. Or use 'run_server.bat' to see logs")
            print("\n🌐 API available at: http://localhost:5003")
            print("📚 Documentation at: http://localhost:5003/docs")
            print("=" * 80)

            # 6. Clean up virtual environment
            cleanup_virtual_environment()

            return True
        else:
            print("\n❌ Build failed. See errors above.")
            return False

    except KeyboardInterrupt:
        print("\n⏹️  Build cancelled by user")
        return False
    except Exception as e:
        error_msg = f"\n❌ Unexpected error: {e}"
        print(error_msg)
        import traceback
        print("🔍 Error details:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("   • Verify that server.py exists")
        print("   • Ensure you have write permissions")
        print("   • Check if antivirus is blocking the process")
        print("   • Make sure there is enough disk space")
        sys.exit(1)
    sys.exit(0)