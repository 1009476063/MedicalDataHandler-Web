import time
from collections import deque
from typing import Optional


class LogService:
    def __init__(self, max_entries: int = 500):
        self.max_entries = max_entries
        self.entries: deque[dict] = deque(maxlen=max_entries)

    def log(self, level: str, message: str, source: str = "system"):
        entry = {
            "id": len(self.entries),
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "source": source,
        }
        self.entries.append(entry)
        return entry

    def info(self, message: str, source: str = "system"):
        return self.log("info", message, source)

    def warning(self, message: str, source: str = "system"):
        return self.log("warning", message, source)

    def error(self, message: str, source: str = "system"):
        return self.log("error", message, source)

    def success(self, message: str, source: str = "system"):
        return self.log("success", message, source)

    def get_logs(
        self, since: Optional[float] = None, level: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        logs = list(self.entries)
        if since is not None:
            logs = [e for e in logs if e["timestamp"] > since]
        if level is not None:
            logs = [e for e in logs if e["level"] == level]
        return logs[-limit:]

    def clear(self):
        self.entries.clear()


log_service = LogService()
