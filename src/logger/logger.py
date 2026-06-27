import logging

class Logger:
    def __init__(self, level = logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname).4s %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Write to file
        file_handler = logging.FileHandler("factoria.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Write to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log_alert(self, msg: str):
        self.logger.warning(f"Alert: {msg}")

    def log_info(self, msg):
        self.logger.info(f"Info: {msg}")