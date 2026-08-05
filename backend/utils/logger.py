import sys

class Logger:
    @staticmethod
    def _safe_print(msg):
        try:
            print(msg, file=sys.stderr)
        except UnicodeEncodeError:
            print(msg.encode('ascii', 'replace').decode('ascii'), file=sys.stderr)

    @staticmethod
    def info(msg):
        Logger._safe_print(f"[INFO] {msg}")
        
    @staticmethod
    def warn(msg):
        Logger._safe_print(f"[WARNING] {msg}")
        
    @staticmethod
    def error(msg):
        Logger._safe_print(f"[ERROR] {msg}")
