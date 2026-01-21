import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
import sys
import os

class Log:
    """
    Provide a lazy and safe logging facade.

    This class offers static methods for logging messages at different levels.
    """

    _initialized = False
    _logger: logging.Logger | None = None

    @classmethod
    def _init(cls) -> None:
        """
        Initialize the logger if it has not been initialized.

        Set up a timed rotating file handler and formatting for logging.
        Prevent duplicate handlers and ensure logs are stored in a dedicated
        directory.

        Parameters
        ----------
        None

        Returns
        -------
        None
            This method does not return a value.
        """
        # Return early if logger is already initialized
        if cls._initialized:
            return

        # Determine base path for logs depending on execution context
        if getattr(sys, "frozen", False):
            base_path = Path(sys.executable).parent
        elif hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(os.path.dirname(os.path.abspath(sys.argv[0])))

        # Create logs directory next to the executable or script
        log_dir = base_path / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

        # Create log file with current date in its name
        try:
            log_file = log_dir / f"server_{datetime.now().strftime('%Y-%m-%d')}.log"
        except Exception:
            return

        logger = logging.getLogger("HTTPProxyLogger")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Configure timed rotating file handler for daily log rotation
        handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
            utc=False,
        )

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # Avoid adding duplicate handlers for the same log file
        if not any(
            isinstance(h, TimedRotatingFileHandler)
            and h.baseFilename == handler.baseFilename
            for h in logger.handlers
        ):
            logger.addHandler(handler)

        cls._logger = logger
        cls._initialized = True

    @classmethod
    def info(cls, message: str) -> None:
        """
        Log an informational message.

        Parameters
        ----------
        message : str
            The message to log.

        Returns
        -------
        None
            This method does not return a value.
        """
        cls._init()
        assert cls._logger is not None
        cls._logger.info(message)

    @classmethod
    def warning(cls, message: str) -> None:
        """
        Log a warning message.

        Parameters
        ----------
        message : str
            The message to log.

        Returns
        -------
        None
            This method does not return a value.
        """
        cls._init()
        assert cls._logger is not None
        cls._logger.warning(message)

    @classmethod
    def error(cls, message: str) -> None:
        """
        Log an error message.

        Parameters
        ----------
        message : str
            The message to log.

        Returns
        -------
        None
            This method does not return a value.
        """
        cls._init()
        assert cls._logger is not None
        cls._logger.error(message)
