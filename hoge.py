from datetime import datetime, timedelta
import time

current_time = time.time()  # Get current time
metric_time = int(current_time)  # Convert for Mackerel (optional)

# Create to_datetime from current_time
to_datetime = datetime.fromtimestamp(current_time)

# Calculate 5 minutes before to_datetime
time_delta = timedelta(minutes=5)
from_datetime = to_datetime - time_delta

# Format to_datetime and from_datetime for output
to_datetime_str = to_datetime.strftime("%Y-%m-%dT%H:%M:%S +09:00")
from_datetime_str = from_datetime.strftime("%Y-%m-%dT%H:%M:%S +09:00")

print(f"to time:{to_datetime_str}")
print(f"from time:{from_datetime_str}")

