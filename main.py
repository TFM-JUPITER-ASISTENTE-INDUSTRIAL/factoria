from src.app import App
from src.config.logger import setup_logging

if __name__ == "__main__":
   app = App()
   setup_logging()
   app.run()
