"""
Молуль для создания кастомных фильтров Jinja.
"""


def log_class(log):
    """Определяет CSS-класс для строки лога."""
    log = log.upper()  # Делаем регистр одинаковым
    if "ERROR" in log:
        return "log-error"
    elif "WARNING" in log:
        return "log-warning"
    elif "INFO" in log:
        return "log-info"
    return ""
