import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging(
        log_level: int = logging.INFO,
        log_directory: Path | None,
) -> None:
    """
    Configures console and rotating file logging.
    """

    if log_directory is None:
        log_directory = Path(__file__).resolve().parents[2] / "logs"

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_directory / "collector.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoids duplicate handlers if configureation runs twice.
    for handler in root_logger.handlers[:]:
        if getattr(handler, "_elevate_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    console_handler._elevate_handler = True
    file_handler._elevate_handler = True

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)