import json
import logging
import sys
from contextvars import ContextVar
from pathlib import Path

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

class StructuredJsonFormatter(logging.Formatter):
    """Formateur de logs produisant un JSON structuré pour l'observabilité."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get()
        }
        if hasattr(record, "props") and isinstance(record.props, dict):
            log_data.update(record.props)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_file_path: str = "log/app.log"):
    log_file = Path(log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = StructuredJsonFormatter()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [stdout_handler, file_handler]

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)