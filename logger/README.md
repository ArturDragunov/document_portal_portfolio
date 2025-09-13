# CustomLogger Class Documentation

This document explains two implementations of a CustomLogger class: a simple version and an advanced structured logging version using structlog.
Use simple logging for development -> it's more human-readable. For production use more complex logging as it is in JSON format and we could update ELK in AWS.

## Simple CustomLogger

### Overview
Basic logging implementation that creates timestamped log files with standard Python logging.

### Code Steps

1. **Initialize Logger**
   ```python
   def __init__(self, log_dir="logs"):
   ```
   - Creates `logs` directory if it doesn't exist
   - Generates timestamped filename: `YYYY_MM_DD_HH_MM_SS.log`
   - Configures basic logging with file output and custom format

2. **Get Logger Instance**
   ```python
   def get_logger(self, name=__file__):
   ```
   - Returns a logger instance named after the calling file
   - Uses `os.path.basename()` to extract filename from full path

### Features
- File-only logging
- Timestamped log files
- Standard text format with timestamp, level, name, line number, and message

---

## Advanced CustomLogger (Structured Logging)

### Overview
Enhanced implementation using structlog for JSON-structured logging with both console and file output.

### Code Steps

1. **Initialize Logger**
   ```python
   def __init__(self, log_dir="logs"):
   ```
   - Creates `logs` directory in current working directory
   - Generates timestamped log file path
   - Stores file path for handler configuration

2. **Configure Handlers**
   ```python
   file_handler = logging.FileHandler(self.log_file_path)
   console_handler = logging.StreamHandler()
   ```
   - **File Handler**: Writes JSON logs to timestamped file
   - **Console Handler**: Displays JSON logs in terminal
   - Both handlers use raw message format (structlog handles JSON rendering)

3. **Setup Basic Logging**
   ```python
   logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
   ```
   - Configures root logger with both handlers
   - Sets INFO level for all logging

4. **Configure Structlog**
   ```python
   structlog.configure(processors=[...])
   ```
   - **TimeStamper**: Adds ISO UTC timestamps
   - **add_log_level**: Includes log level in output
   - **EventRenamer**: Renames message field to "event"
   - **JSONRenderer**: Converts to JSON format

5. **Return Logger**
   ```python
   return structlog.get_logger(logger_name)
   ```
   - Creates structlog logger instance with filename as name

### Features
- **Dual Output**: Console + file logging
- **JSON Structure**: Machine-readable structured logs
- **Rich Context**: Easy addition of contextual data
- **UTC Timestamps**: Consistent timezone handling
- **Auto-formatting**: Structured data automatically serialized

### Usage Example
```python
logger = CustomLogger().get_logger(__file__)
logger.info("User uploaded a file", user_id=123, filename="report.pdf")
logger.error("Failed to process PDF", error="File not found", user_id=123)
```

### Output Format
```json
{
  "timestamp": "2025-01-15T10:30:45.123456Z",
  "level": "info", 
  "event": "User uploaded a file",
  "user_id": 123,
  "filename": "report.pdf"
}
```

## Key Differences

| Feature | Simple | Advanced |
|---------|--------|----------|
| Output Format | Text | JSON |
| Destinations | File only | Console + File |
| Structured Data | No | Yes |
| Dependencies | logging only | logging + structlog |
| Context Support | Limited | Rich |
| Machine Readable | No | Yes |

## Dependencies

**Simple Version:**
- `os`
- `logging` 
- `datetime`

**Advanced Version:**
- `os`
- `logging`
- `datetime`
- `structlog`

Install structlog: `pip install structlog`