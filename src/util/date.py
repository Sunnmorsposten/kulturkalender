from datetime import datetime

def convert_norwegian_date_to_postgres(date_str):
    """
    Convert a Norwegian date string to a PostgreSQL date string.
    Expected format: "DD Mon. YYYY" (e.g., "12 jan. 2023").
    """
    norwegian_months = {
        'jan.': '01',
        'feb.': '02',
        'mar.': '03',
        'apr.': '04',
        'mai': '05',
        'jun.': '06',
        'jul.': '07',
        'aug.': '08',
        'sep.': '09',
        'okt.': '10',
        'nov.': '11',
        'des.': '12'
    }

    parts = date_str.strip().split(' ')
    if len(parts) != 3:
        print("Date string is not in expected format.")
        return None

    day = parts[0].rstrip('.')
    month = parts[1].lower()
    year = parts[2]

    month_num = norwegian_months.get(month)
    if not month_num:
        print(f"Unrecognized month abbreviation: {month}")
        return None

    date_str_formatted = f"{year}-{month_num}-{day.zfill(2)}"

    try:
        date_obj = datetime.strptime(date_str_formatted, "%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return None

    return date_obj.strftime('%Y-%m-%d %H:%M:%S')



def convert_date_to_postgres(date_str):
    """
    Converts a standard European date format (DD.MM.YYYY) into a PostgreSQL-compatible format (YYYY-MM-DD).
    
    Expected format: "DD.MM.YYYY" (e.g., "25.12.2022").
    """
    try:
        # Attempt to parse the date string assuming the format is DD.MM.YYYY
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        # Format it to PostgreSQL-compatible format YYYY-MM-DD
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # If format is incorrect, return the original string
        return date_str

def convert_array_to_postgresql_date(date_array):
    """
    Converts a date represented as an array into a PostgreSQL date format.
    
    Expected format: ["DD", "Month", "YYYY"].
    Example input: ["12", "January", "2023"].
    """
    # Join the day, month, and year into a single string
    date_str = f"{date_array[0]} {date_array[2]} {date_array[3]}"
    try:
        # Parse the date string using the format "DD Month YYYY"
        date_obj = datetime.strptime(date_str, "%d %B %Y")
        # Return the formatted date in "YYYY-MM-DD" format
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Return None if the date format is incorrect
        return None