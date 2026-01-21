import subprocess
import sys
import os
from pathlib import Path
import venv
import shutil
from builder.config import (
    SCRIPT_NAME, EXE_NAME, VERSION,
    DESCRIPTION, COMPANY, COPYRIGHT,
    ICON_FILE, VENV_NAME, HIDDEN_IMPORTS,
    SOURCE_FOLDERS
)

class ExecutableBuilder:

    def __init__(self) -> None:
        """
        Initialize the ExecutableBuilder instance.

        Sets up configuration parameters and paths for building the executable.

        Returns
        -------
        None
            This method does not return a value.
        """
        self.config = {
            "script_name": SCRIPT_NAME,
            "exe_name": EXE_NAME,
            "version": VERSION,
            "description": DESCRIPTION,
            "company": COMPANY,
            "copyright": COPYRIGHT,
            "icon_file": ICON_FILE,
            "venv_name": VENV_NAME,
            "hidden_imports": HIDDEN_IMPORTS,
            "source_folders": SOURCE_FOLDERS
        }
        self.venv_path = Path(self.config["venv_name"])
        # Set paths for Python, pip, and PyInstaller executables based on OS
        if sys.platform == "win32":
            self.venv_python = self.venv_path / "Scripts" / "python.exe"
            self.venv_pip = self.venv_path / "Scripts" / "pip.exe"
            self.venv_pyinstaller = self.venv_path / "Scripts" / "pyinstaller.exe"
        else:
            self.venv_python = self.venv_path / "bin" / "python"
            self.venv_pip = self.venv_path / "bin" / "pip"
            self.venv_pyinstaller = self.venv_path / "bin" / "pyinstaller"

    def setupVirtualEnvironment(self) -> bool:
        """
        Set up a new virtual environment for building.

        Removes any existing virtual environment and creates a new one with pip
        installed.

        Returns
        -------
        bool
            True if the environment was created successfully, False otherwise.
        """
        try:
            # Remove existing virtual environment if present
            if self.venv_path.exists():
                shutil.rmtree(self.venv_path)
            # Create new virtual environment with pip
            venv.create(self.venv_path, with_pip=True)
            if not self.venv_python.exists():
                error_msg = "Error: Could not create the virtual environment."
                print(error_msg)
                return False
            return True
        except Exception as e:
            error_msg = f"Error creating virtual environment: {e}"
            print(error_msg)
            return False

    def installBuildDependencies(self) -> bool:
        """
        Install build dependencies in the virtual environment.

        Installs required build packages and project dependencies from
        requirements.txt if present.

        Returns
        -------
        bool
            True if all dependencies are installed successfully, False otherwise.
        """
        build_packages = ["pyinstaller", "setuptools", "wheel"]
        # Install project dependencies from requirements.txt if it exists
        if Path("requirements.txt").exists():
            try:
                subprocess.run(
                    [str(self.venv_pip), "install", "-r", "requirements.txt"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                error_msg = f"Error installing project dependencies: {e.stderr}"
                print(error_msg)
                return False
        # Install build packages required for executable creation
        for package in build_packages:
            try:
                subprocess.run(
                    [str(self.venv_pip), "install", package],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                error_msg = f"Error installing {package}: {e.stderr}"
                print(error_msg)
                return False
        # Verify PyInstaller installation
        try:
            subprocess.run(
                [
                    str(self.venv_python),
                    "-c",
                    "import PyInstaller; print(PyInstaller.__version__)",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            error_msg = "Error: PyInstaller was not installed correctly."
            print(error_msg)
            return False

    def checkDependencies(self) -> bool:
        """
        Check and ensure required dependencies are installed.

        Verifies the existence of the virtual environment and PyInstaller.
        Installs dependencies if missing.

        Returns
        -------
        bool
            True if dependencies are present or installed successfully,
            False otherwise.
        """
        # Check if the virtual environment exists
        if not self.venv_python.exists():
            if not self.setupVirtualEnvironment():
                return False
            if not self.installBuildDependencies():
                return False
        else:
            try:
                # Check if PyInstaller is installed in the virtual environment
                result = subprocess.run(
                    [
                        str(self.venv_python),
                        "-c",
                        "import PyInstaller; print(PyInstaller.__version__)",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    if not self.installBuildDependencies():
                        return False
            except Exception as e:
                error_msg = f"Error checking PyInstaller: {e}"
                print(error_msg)
                return False
        return True

    def render_template(self, template_path: str, replacements: dict) -> str:
        """
        Renderiza un template reemplazando los marcadores por los valores dados.
        """
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        for key, value in replacements.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content

    def createVersionFile(self) -> bool:
        """
        Crear el archivo de información de versión usando el template.

        Generates a version_info.txt file containing build metadata such as
        version, company, description, and copyright.

        Returns
        -------
        bool
            True if the file was created successfully, False otherwise.
        """
        # Format version string for filevers/prodvers fields
        version_parts = self.config["version"].replace(".", ", ")
        replacements = {
            "version_parts": version_parts,
            "company": self.config["company"],
            "description": self.config["description"],
            "version": self.config["version"],
            "exe_name": self.config["exe_name"],
            "copyright": self.config["copyright"]
        }
        try:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "version_info_template.txt")
            content = self.render_template(template_path, replacements)
            with open("version_info.txt", "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error creando archivo de versión: {e}")
            return False

    def createPyinstallerSpec(self) -> str | None:
        """
        Genera el archivo spec usando el template.

        Generate the PyInstaller spec file for building the executable.

        Constructs a .spec file with required settings, including source folders,
        hidden imports, and icon configuration.

        Returns
        -------
        str or None
            Absolute path to the created spec file, or None if creation fails.
        """
        icon_path = "None"
        # Use icon file if it exists
        if os.path.exists(self.config["icon_file"]):
            icon_path = f"'{self.config['icon_file']}'"
        # Add source folders as datas for PyInstaller
        datas_lines = [f"    ('{folder}', '{folder}'),"
                       for folder in self.config["source_folders"]]
        datas_block = "\n".join(datas_lines)
        replacements = {
            "script_name": self.config["script_name"],
            "datas_block": datas_block,
            "hidden_imports": str(self.config["hidden_imports"]),
            "exe_name": self.config["exe_name"],
            "icon_path": icon_path
        }
        try:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "spec_template.spec")
            content = self.render_template(template_path, replacements)
            spec_filename = os.path.abspath(f"{self.config['exe_name']}.spec")
            with open(spec_filename, "w", encoding="utf-8") as f:
                f.write(content)
            return spec_filename
        except Exception as e:
            print(f"Error creando archivo spec: {e}")
            return None

    def buildExecutable(self) -> bool:
        """
        Build the executable using PyInstaller.

        Generates the PyInstaller spec file if missing, then runs PyInstaller
        to compile the executable. Checks for successful build and existence
        of the output file.

        Returns
        -------
        bool
            True if the executable was built successfully, False otherwise.
        """
        # Get absolute path to spec file
        spec_path: str = os.path.abspath(f"{self.config['exe_name']}.spec")
        # Create spec file if it does not exist
        if not os.path.exists(spec_path):
            spec_path = self.createPyinstallerSpec()
            if not spec_path:
                return False
        # Prepare PyInstaller command
        cmd: list[str] = [str(self.venv_pyinstaller), "--clean", "--noconfirm", spec_path]
        try:
            # Run PyInstaller in the current working directory
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                exe_path = Path("dist") / f"{self.config['exe_name']}.exe"
                # Check if the executable was created
                if exe_path.exists():
                    print(f"Build succeeded. Executable: {exe_path}")
                    return True
                else:
                    print("Error: Executable not found in dist/")
                    return False
            else:
                error_msg = f"Error during build: {result.stderr}"
                print(error_msg)
                return False
        except Exception as e:
            error_msg = f"Error running PyInstaller: {e}"
            print(error_msg)
            return False

    def cleanupBuildFiles(self) -> None:
        """
        Remove build artifacts and temporary files.

        Deletes build directories and files generated during the build process,
        including the build folder, __pycache__, spec file, and version info.

        Returns
        -------
        None
            This method does not return a value.
        """
        cleanup_items: list[str] = [
            "build",
            "__pycache__",
            f"{self.config['exe_name']}.spec",
            "version_info.txt",
        ]
        # Remove each item if it exists
        for item in cleanup_items:
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                elif os.path.isfile(item):
                    os.remove(item)
            except Exception:
                # Ignore errors during cleanup
                pass

    def cleanupVirtualEnvironment(self) -> None:
        """
        Remove the temporary virtual environment.

        Deletes the virtual environment directory if it exists.

        Returns
        -------
        None
            This method does not return a value.
        """
        # Remove the virtual environment directory if present
        try:
            if self.venv_path.exists():
                shutil.rmtree(self.venv_path)
        except Exception:
            # Ignore errors during cleanup
            pass

        # Execute pyclean to remove compiled files
        try:
            subprocess.run(
                [sys.executable, "-m", "pyclean", "."],
                capture_output=True,
                text=True,
            )
        except Exception:
            # Ignore errors during pyclean
            pass

    def build(self) -> bool:
        """
        Build the HTTP Proxy Server executable.

        Compiles the main script into an executable, ensuring all dependencies
        and version information are set up. Cleans up build artifacts and
        creates a run script for launching the server.

        Returns
        -------
        bool
            True if the build succeeds and the executable is created,
            False otherwise.
        """
        print("Compiling HTTP Proxy Server executable...")
        # Check if main script exists
        if not os.path.exists(self.config["script_name"]):
            error_msg = f"Error: {self.config['script_name']} not found"
            print(error_msg)
            return False
        # Ensure dependencies are installed
        if not self.checkDependencies():
            error_msg = "Error preparing dependencies."
            print(error_msg)
            return False
        # Create version info file
        if not self.createVersionFile():
            error_msg = "Error creating version file."
            print(error_msg)
            return False
        # Build the executable
        if not self.buildExecutable():
            error_msg = "Error during compilation."
            print(error_msg)
            return False
        # Remove build artifacts and temporary files
        self.cleanupBuildFiles()
        # Remove the temporary virtual environment
        self.cleanupVirtualEnvironment()
        print(f"Executable ready at dist/{self.config['exe_name']}.exe")
        return True