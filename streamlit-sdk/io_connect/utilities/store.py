import sys
import logging
from timeit import default_timer
from typing import Optional


class Logger:
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        message: str = "",
        log_time: bool = False,
    ):
        self.interval = 0
        self.message = message
        self.log_time = log_time
        self.logger = logger

    def __enter__(self):
        self.start = default_timer()
        return self

    def __exit__(self, *args):
        self.end = default_timer()

        if self.log_time:
            self.interval = self.end - self.start
            self.info(f"[NETWORK] {self.message} {self.interval:.4f} seconds")

    def info(self, log: str):
        if self.logger:
            self.logger.info(log)
        else:
            print(log)

    def error(self, log: str):
        if self.logger:
            self.logger.error(log)
        else:
            print(log)

    def display_log(self, log: str):
        """
        Display a log message on the console.

        This function writes a log message to the standard output stream (stdout),
        overwriting any existing content on the current line.

        Args:
            log (str): The log message to be displayed.

        Returns:
            None

        Example:
            >>> display_log("Processing...")  # Displays "Processing..." on the console

        """

        # Move the cursor to the beginning of the line
        sys.stdout.write("\r")

        # Clear the content from the cursor to the end of the line
        sys.stdout.write("\033[K")

        # Write the log message
        sys.stdout.write(log)

        # Flush the output buffer to ensure the message is displayed immediately
        sys.stdout.flush()


def ERROR_MESSAGE(response, url):
    return f"""
[STATUS CODE] {response.status_code}
[URL] {url}
[SERVER INFO] {response.headers.get("Server", "Unknown Server")}
[RESPONSE] {response.text}
"""
