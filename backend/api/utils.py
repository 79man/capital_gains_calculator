import magic
from werkzeug.utils import secure_filename
import time, os, threading
# Add file size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_type(file, allowed_types):
    """Validate file type using magic numbers"""
    if not file:
        return False

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB")

    # Check magic number
    file_header = file.read(1024)
    file.seek(0)  # Reset
    mime_type = magic.from_buffer(file_header, mime=True)

    return mime_type in allowed_types


def sanitize_config_input(value, param_type, min_val=None, max_val=None) -> bool | int | str:
    """Sanitize and validate configuration inputs"""
    if param_type == 'bool':
        return str(value).lower() in ('true', '1', 'yes', 'on')
    elif param_type == 'int':
        try:
            val = int(value)
            if min_val is not None and val < min_val:
                raise ValueError(f"Value must be >= {min_val}")
            if max_val is not None and val > max_val:
                raise ValueError(f"Value must be <= {max_val}")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer value: {value}")
    return str(value)


def cleanup_after_delay(file_path, delay=1.0):
    def delayed_cleanup():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            pass

    thread = threading.Thread(target=delayed_cleanup)
    thread.daemon = True
    thread.start()