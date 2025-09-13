import sys
import traceback
from logger.custom_logger_archive import CustomLoggerArchive
logger = CustomLoggerArchive().get_logger(__file__)
class DocumentPortalException(Exception):
    def __init__(self, error_message, error_details):
        _, _, exc_tb = error_details.exc_info() # we take only traceback object and fetch all the necessary info from there.
        # sys.exc_info() looks like: (<class 'ZeroDivisionError'>, ZeroDivisionError('division by zero'), <traceback object at 0x00000231341AAD40>)
        self.file_name = exc_tb.tb_frame.f_code.co_filename
        self.lineno = exc_tb.tb_lineno
        self.error_message = str(error_message)
        self.traceback_str = ''.join(traceback.format_exception(*sys.exc_info()))

    def __str__(self): # string representation of an object (of DocumentPortalException instance)
        return f"""
        Error in [{self.file_name}] at line [{self.lineno}]
        Message: {self.error_message}
        Traceback:
        {self.traceback_str}
        """

if __name__ == "__main__":
    try:
        a = 1 / 0  # deliberate error
    except Exception as e:
        app_exc = DocumentPortalException(e, sys)
        logger.error(app_exc)  # log it to file
        raise app_exc  # propagate with full traceback -> we do both logging and racing exception here
    # try:
    #     a = int("abc")  # ValueError (inbuilt)
    # except ValueError as e:
    #     raise DocumentPortalException("Failed while processing document", e)

# With CustomLoggerArchive you get this log:
# [ 2025-08-12 08:48:29,911 ] ERROR custom_exception_archive.py (line:26) - 
#         Error in [...custom_exception_archive.py] at line [23]
#         Message: division by zero
#         Traceback:
#         Traceback (most recent call last):
#   File "...custom_exception_archive.py", line 23, in <module>
#     a = 1 / 0  # deliberate error
#         ~~^~~
# ZeroDivisionError: division by zero

# But with updated logger, you get log as:
# {"timestamp": "2025-08-12T06:46:18.126568Z", "level": "error", "event": "DocumentPortalException(ZeroDivisionError('division by zero'), <module 'sys' (built-in)>)"}
