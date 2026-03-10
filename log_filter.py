import sys
import re
from datetime import datetime, timezone, timedelta

def main():
    ist = timezone(timedelta(hours=5, minutes=30))
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)Z(\s+\[.*)')
    
    for line in sys.stdin:
        m = pattern.match(line)
        if m:
            try:
                dt_utc = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
                dt_ist = dt_utc.astimezone(ist)
                formatted_time = dt_ist.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                sys.stdout.write(f"[{formatted_time}] {m.group(2).lstrip()}\n")
                sys.stdout.flush()
                continue
            except Exception:
                pass
        sys.stdout.write(line)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
