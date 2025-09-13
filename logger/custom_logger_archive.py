import os
import logging
from datetime import datetime
import structlog
class CustomLoggerArchive: # good for development purposes but format is not suitable for production
    def __init__(self,log_dir="logs"):
        # Ensure logs directory exists, if not -> create it
        self.logs_dir = os.path.join(os.getcwd(), log_dir) # log directory created at current root directory
        os.makedirs(self.logs_dir, exist_ok=True)

        # Create timestamped log file name
        log_file = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
        log_file_path = os.path.join(self.logs_dir, log_file)

        # Configure logging -> format and level of importance to log
        logging.basicConfig(
            filename=log_file_path,
            format="[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
            level=logging.INFO,
        )
        
    def get_logger(self,name=__file__):
        return logging.getLogger(os.path.basename(name))
if __name__ == "__main__":
    logger = CustomLoggerArchive()
    logger=logger.get_logger(__file__)
    logger.info("Custom logger initialized.")


# import os
# import logging
# from datetime import datetime
# import structlog # structure log in JSON format

# class CustomLogger: # good for production! JSON format can be processed in cloud
#     def __init__(self, log_dir="logs"):
#         # Ensure logs directory exists
#         self.logs_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.logs_dir, exist_ok=True)
        
#         # Prepare log file path but don't create the file yet
#         # Timestamped log file (for persistence)
#         log_file = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
#         self.log_file_path = os.path.join(self.logs_dir, log_file)
#         self._file_handler_created = False

#     def _create_file_handler_if_needed(self):
#         """Create file handler only when first log message is written"""
#         if not self._file_handler_created:
#             # Only create the file when we actually need to write to it
#             file_handler = logging.FileHandler(self.log_file_path)
#             file_handler.setLevel(logging.INFO)
#             file_handler.setFormatter(logging.Formatter("%(message)s"))  # Raw JSON lines
            
#             # Add to root logger
#             root_logger = logging.getLogger()
#             root_logger.addHandler(file_handler)
            
#             self._file_handler_created = True

#     def get_logger(self, name=__file__): # capture the file name in whatever file we are having the log
#         logger_name = os.path.basename(name)

#         # Configure console handler (no file handler yet)
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.INFO)
#         console_handler.setFormatter(logging.Formatter("%(message)s"))

#         logging.basicConfig( # log configuration
#             level=logging.INFO,
#             format="%(message)s",  # Structlog will handle JSON rendering
#             handlers=[console_handler],  # Only console for now
#             force=True  # Override existing configuration
#         )

#         # Configure structlog for JSON structured logging
#         structlog.configure(
#             processors=[
#                 structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"), # timestamp
#                 structlog.processors.add_log_level, # level
#                 structlog.processors.EventRenamer(to="event"), # event
#                 # Add a processor to create file handler on first use
#                 self._lazy_file_creation_processor,
#                 structlog.processors.JSONRenderer()  # output in JSON format
#             ],
#             logger_factory=structlog.stdlib.LoggerFactory(),
#             cache_logger_on_first_use=True,
#         )

#         return structlog.get_logger(logger_name)

#     def _lazy_file_creation_processor(self, _logger, _name, event_dict):
#         """Processor that creates file handler on first log message
#         _logger and _name are unused but needed because of structlog signature"""
#         self._create_file_handler_if_needed()
#         return event_dict
    
# #  Usage Example ---
# if __name__ == "__main__":
#     logger = CustomLogger().get_logger(__file__)
#     logger.info("User uploaded a file", user_id=123, filename="report.pdf")
#     logger.error("Failed to process PDF", error="File not found", user_id=123)


# import os
# import logging
# from datetime import datetime
# import structlog # structure log in JSON format

# class CustomLogger: # good for production! JSON format can be processed in cloud
#     def __init__(self, log_dir="logs"):
#         # Ensure logs directory exists
#         self.logs_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.logs_dir, exist_ok=True)

#         # Timestamped log file (for persistence)
#         log_file = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
#         self.log_file_path = os.path.join(self.logs_dir, log_file)

#     def get_logger(self, name=__file__): # capture the file name in whatever file we are having the log
#         logger_name = os.path.basename(name)

#         # Configure logging for console + file (both JSON)
#         file_handler = logging.FileHandler(self.log_file_path)
#         file_handler.setLevel(logging.INFO)
#         file_handler.setFormatter(logging.Formatter("%(message)s"))  # Raw JSON lines
#         # for console
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.INFO)
#         console_handler.setFormatter(logging.Formatter("%(message)s"))

#         logging.basicConfig( # log configuration
#             level=logging.INFO,
#             format="%(message)s",  # Structlog will handle JSON rendering
#             handlers=[console_handler, file_handler]
#         )

#         # Configure structlog for JSON structured logging
#         structlog.configure(
#             processors=[
#                 structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"), # timestamp
#                 structlog.processors.add_log_level, # level
#                 structlog.processors.EventRenamer(to="event"), # event
#                 structlog.processors.JSONRenderer() # output in JSON format
#             ],
#             logger_factory=structlog.stdlib.LoggerFactory(),
#             cache_logger_on_first_use=True,
#         )

#         return structlog.get_logger(logger_name)


# # --- Usage Example ---
# if __name__ == "__main__":
#     logger = CustomLogger().get_logger(__file__)
#     logger.info("User uploaded a file", user_id=123, filename="report.pdf")
#     logger.error("Failed to process PDF", error="File not found", user_id=123)    