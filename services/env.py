import os
import sys
from dotenv import load_dotenv
from typing import Final

class Env:
    """
    Provide safe, lazy-loading access to environment variables.

    This class works in scripts and PyInstaller binaries. It loads .env
    automatically on first access, does not cast values, and does not
    override system environment variables.
    """

    _loaded: Final[bool] = False

    @classmethod
    def _load_env(cls, dotenv_filename: str = ".env") -> None:
        """
        Load environment variables from a .env file if not already loaded.

        Parameters
        ----------
        dotenv_filename : str, optional
            Name of the .env file to load. Defaults to ".env".

        Returns
        -------
        None
            This method does not return a value.
        """
        # Prevent reloading if already loaded
        if cls._loaded:
            return

        # Determine base path for .env file, supporting PyInstaller
        base_path: str = getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(os.path.abspath(sys.argv[0])),
        )

        env_path: str = os.path.join(base_path, dotenv_filename)

        # Load .env file if it exists, without overriding system variables
        if os.path.isfile(env_path):
            load_dotenv(env_path, override=False)

        cls._loaded = True

    @classmethod
    def get(cls, name: str, default: str | None = None) -> str | None:
        """
        Retrieve the value of an environment variable.

        Parameters
        ----------
        name : str
            Name of the environment variable to retrieve.
        default : str | None, optional
            Default value to return if the variable is not set.

        Returns
        -------
        str | None
            Value of the environment variable, or default if not set.
        """
        # Ensure environment variables are loaded before access
        cls._load_env()
        return os.environ.get(name, default)
