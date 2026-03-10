import sys
import re
from datetime import datetime, timezone, timedelta

def main():
    ist = timezone(timedelta(hours=5, minutes=30))
    # Matches Airflow's default output: 2026-03-09T17:56:38.502557Z [info     ]
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)Z(\s+\[.*)')
    
    for line in sys.stdin:
        m = pattern.match(line)
        if m:
            try:
                # Parse UTC
                dt_utc = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
                # Convert to IST
                dt_ist = dt_utc.astimezone(ist)
                # Format to standard localized logging look
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
