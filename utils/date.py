from datetime import datetime, timedelta
import pytz

def convert_relative_time_to_date(number, unit):
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    if unit.startswith("hour") or unit.startswith("jam"):
        return now - timedelta(hours=number)
    elif unit.startswith("day") or unit.startswith("hari"):
        return now - timedelta(days=number)
    elif unit.startswith("month") or unit.startswith("bulan"):
        return now - timedelta(days=number*30)
    else:
        return now