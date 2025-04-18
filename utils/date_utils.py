from datetime import datetime

def parse_datetime_string(text):
    try:
        dt = datetime.strptime(text.strip(), "%d.%m %H:%M")
        return dt.strftime("%d.%m"), dt.strftime("%H:%M")
    except:
        return None