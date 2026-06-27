import logging
import time

from src.logger.logger import Logger

class App:
    def __init__(self):
        self.running = True
        self.logger = Logger(level=logging.INFO)
    def run(self):
        self.logger.log_info(msg="FactorIA start")
        while self.running:
            self.logger.log_alert(msg="FactorIA alert")
            time.sleep(1)

    def stop(self):
        self.running = False

