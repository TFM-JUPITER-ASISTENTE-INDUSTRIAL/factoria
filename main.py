from src.app import App
from src.config.logger import setup_logging
from src.storage.connectors.postgresql import SessionLocal

if __name__ == "__main__":
   setup_logging()
   session = SessionLocal()
   app = App(session=session)
   try:
      app.run()
   finally:
      session.close()
