import logging

def setup_logging():
   formatter = logging.Formatter(
      '%(asctime)s - %(levelname)-7s - %(name)s - %(message)s',
      datefmt="%Y-%m-%d %H:%M:%S"
   )

   # Write to console
   console_handler = logging.StreamHandler()
   console_handler.setFormatter(formatter)

   root_logger = logging.getLogger()
   root_logger.addHandler(console_handler)
   root_logger.setLevel(logging.INFO)