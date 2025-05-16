import logging
import json
import sys
import os
from typeguard import typechecked
from logging.handlers import TimedRotatingFileHandler
import io_connect.constants as c

@typechecked
class LoggerConfigurator:
    __version__ = c.VERSION
    """
    A class for configuring and setting up logging for a service.
    It supports both console and file logging with structured JSON format.

    Attributes:
        service_name (str): The name of the service used in the log entries.
        log_dir (str): The directory where the log files will be saved. Defaults to './logs' in the application root.
        log_level (int): The logging level (e.g., DEBUG, INFO). Defaults to logging.DEBUG. logging.DEBUG has a value of 10. logging.INFO has a value of 20. logging.WARNING has a value of 30. logging.ERROR has a value of 40. logging.CRITICAL has a value of 50.
        rotation_period (str, optional): Time interval for rotation. Defaults to 'M' (minutes). Options "S": Seconds,"M": Minutes,"H": Hours,"D": Days
        rotation_interval (int, optional): How often to rotate logs based on `when`. Defaults to 5.
        rotation_backup_count (int, optional): Number of old logs to keep. Defaults to 10.
        message_format(boolean, optional)=Determines if the console log message should be formatted in JSON. Defaults to False.
        console_logger(boolean, optional)=Determineswe should log console log message should be formatted in JSON. Defaults to True.
    Methods:
        get_logger():
            Returns the configured logger instance.
    Example:
        # Initializing Logger
        logger = LoggerConfigurator(service_name="MyService", log_dir="./custom_logs", log_level=logging.INFO, rotation_when="H", rotation_interval=1, rotation_backup_count=5,).get_loggger()
        #logs will rotate after every hour
        # Example of logging at different levels
        logger.debug("This is a debug message")

        # Example of logging with extra data, which will be included in the JSON log
        logger.info("User login successful", extra={"user": "admin", "action": "login", "ip": "192.168.1.1"})

        # Example of logging an error with extra data
        logger.error("Error while processing request", extra={"error_code": 500, "request_id": "abc123"})

    """

    def __init__(
        self,
        service_name: str,
        log_dir: str = "logs",
        log_level: int = logging.DEBUG,
        rotation_period: str = "M",
        rotation_interval: int = 5,
        rotation_backup_count: int = 10,
        format_message: bool = False,
        console_logger: bool = True,
    ):
        """
        Initializes the LoggerConfigurator class to set up logging for the service.

        Args:
            service_name (str): The name of the service (used in the logs).
            log_dir (str, optional): Directory where logs are stored (defaults to './logs').
            log_level (int, optional): The logging level (e.g., logging.DEBUG). Default is logging.DEBUG.
            rotation_period (str, optional): Time interval for rotation. Defaults to 'M' (minutes).Options "S": Seconds,"M": Minutes,"H": Hours,"D": Days
            rotation_interval (int, optional): How often to rotate logs based on `when`. Defaults to 5.
            rotation_backup_count (int, optional): Number of old logs to keep. Defaults to 10.
            format_message(boolean, optional)=Determines if the console log message should be formatted in JSON. Defaults to True.

        """
        self.service_name = service_name
        # Default to "logs" directory in the application's root if log_dir is not specified
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.abspath(sys.argv[0])), "logs"
        )
        self.log_level = log_level
        self.rotation_when = rotation_period
        self.rotation_interval = rotation_interval
        self.rotation_backup_count = rotation_backup_count
        self.message_format = format_message
        self.console_logger = console_logger
        self.logger = self._initialize_logger()

    class DynamicJSONFormatter(logging.Formatter):
        """
        Custom formatter to output logs in a structured JSON format.

        This formatter includes the following fields in each log entry:
            - timestamp: The time when the log was generated.
            - service: The name of the service generating the log.
            - level: The log level (e.g., DEBUG, INFO).
            - message: The log message.

        It also includes any additional information passed via the `extra` field or other log attributes.

        Methods:
            format(record):
                Converts the log record into a JSON string with additional details.
        """

        def __init__(self, service_name):
            super().__init__()
            self.service_name = service_name

        def format(self, record):
            """
            Formats the log record into a structured JSON object.

            Args:
                record (logging.LogRecord): The log record to format.

            Returns:
                str: A JSON string representation of the log record.
            """
            # Base log structure
            log_record = {
                "timestamp": self.formatTime(record),
                "service": self.service_name,
                "level": record.levelname,
                "message": record.getMessage(),
            }

            # Dynamically include extra attributes
            if hasattr(record, "extra") and isinstance(record.extra, dict):
                log_record.update(record.extra)
            else:
                # Include attributes directly from the record dict
                for key, value in record.__dict__.items():
                    if key not in [
                        "args",
                        "msg",
                        "levelname",
                        "levelno",
                        "pathname",
                        "filename",
                        "module",
                        "exc_info",
                        "exc_text",
                        "stack_info",
                        "lineno",
                        "funcName",
                        "created",
                        "msecs",
                        "relativeCreated",
                        "thread",
                        "threadName",
                        "processName",
                        "process",
                        "name",
                    ] and not key.startswith("_"):
                        log_record[key] = value

            return json.dumps(log_record)

    def _configure_handler(self, handler, formatter):
        """
        Configures the log handler with the specified formatter and log level.

        Args:
            handler (logging.Handler): The logging handler to configure (e.g., StreamHandler, TimedRotatingFileHandler).
            formatter (logging.Formatter): The formatter to apply to the handler.

        Returns:
            logging.Handler: The configured logging handler.
        """
        handler.setLevel(self.log_level)
        handler.setFormatter(formatter)
        return handler

    def _initialize_logger(self):
        """
        Initializes the logger with both console and file handlers. The console handler
        will output logs to stdout, and the file handler will save logs to a file with
        rotation (creating new files after a set interval).

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger(self.service_name)
        logger.setLevel(self.log_level)

        # Formatter for structured JSON logs
        formatter = self.DynamicJSONFormatter(self.service_name)

        if self.console_logger:
            # Configure console handler
            console_handler = logging.StreamHandler(sys.stdout)
            if self.message_format:
                # If message_format is True, apply JSON format
                console_handler.setFormatter(formatter)
            else:
                # If message_format is False, use a simple log message format (plain text)
                console_handler.setFormatter(logging.Formatter("%(message)s"))

            logger.addHandler(console_handler)

        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

        # Configure file handler with rotation
        log_file_handler = self._configure_handler(
            TimedRotatingFileHandler(
                filename=f"{self.log_dir}/{self.service_name}_logs.log",
                when=self.rotation_when,
                interval=self.rotation_interval,
                backupCount=self.rotation_backup_count,
            ),
            formatter,
        )
        logger.addHandler(log_file_handler)

        return logger

    def get_logger(self):
        """
        Retrieves the configured logger instance.

        Returns:
            logging.Logger: The logger instance configured with both console and file handlers.
        """
        return self.logger
