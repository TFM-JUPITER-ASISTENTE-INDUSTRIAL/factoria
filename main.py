from src.app import App
import logging

def setup_logging():
   formatter = logging.Formatter(
      '%(asctime)s - %(levelname)-7s - %(name)s - %(message)s',
      datefmt="%Y-%m-%d %H:%M:%S"
   )

   # Write to file
   file_handler = logging.FileHandler("factoria.log")
   file_handler.setFormatter(formatter)

   # Write to console
   console_handler = logging.StreamHandler()
   console_handler.setFormatter(formatter)

   root_logger = logging.getLogger()
   root_logger.addHandler(file_handler)
   root_logger.addHandler(console_handler)
   root_logger.setLevel(logging.INFO)

if __name__ == "__main__":
   app = App()
   setup_logging()
   app.run()
