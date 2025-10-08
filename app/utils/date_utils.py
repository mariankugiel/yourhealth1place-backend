"""
Date utility functions for the application
"""
from datetime import datetime, date
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def parse_date_string(date_input: Union[str, datetime, date, None]) -> Optional[date]:
    """
    Parse various date formats and return a date object
    
    Args:
        date_input: String, datetime, date, or None
        
    Returns:
        date object or None if parsing fails
        
    Raises:
        ValueError: If the input cannot be parsed
    """
    if date_input is None:
        return None
        
    # If it's already a date, return as is
    if isinstance(date_input, date):
        return date_input
        
    # If it's a datetime, extract the date part
    if isinstance(date_input, datetime):
        return date_input.date()
        
    # If it's a string, try to parse it
    if isinstance(date_input, str):
        date_str = date_input.strip()
        if not date_str:
            return None
            
        try:
            # Try parsing YYYY-MM-DD format
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
                
            # Try parsing DD-MM-YYYY format
            if len(date_str) == 10 and date_str.count('-') == 2:
                parts = date_str.split('-')
                if len(parts[0]) == 2:  # DD-MM-YYYY
                    day, month, year = parts
                    return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
                    
            # Try ISO format (with or without time)
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            
        except Exception as e:
            logger.warning(f"Could not parse date string '{date_str}': {e}")
            raise ValueError(f"Could not parse date string: {date_str}")
    
    raise ValueError(f"Invalid date type: {type(date_input)}")


def parse_datetime_string(datetime_input: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse various datetime formats and return a datetime object
    
    Args:
        datetime_input: String, datetime, or None
        
    Returns:
        datetime object or None if parsing fails
        
    Raises:
        ValueError: If the input cannot be parsed
    """
    if datetime_input is None:
        return None
        
    # If it's already a datetime, return as is
    if isinstance(datetime_input, datetime):
        return datetime_input
        
    # If it's a string, try to parse it
    if isinstance(datetime_input, str):
        datetime_str = datetime_input.strip()
        if not datetime_str:
            return None
            
        try:
            # Try parsing YYYY-MM-DD format (assume midnight)
            if len(datetime_str) == 10 and datetime_str.count('-') == 2:
                return datetime.strptime(datetime_str, '%Y-%m-%d')
                
            # Try parsing DD-MM-YYYY format (assume midnight)
            if len(datetime_str) == 10 and datetime_str.count('-') == 2:
                parts = datetime_str.split('-')
                if len(parts[0]) == 2:  # DD-MM-YYYY
                    day, month, year = parts
                    return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')
                    
            # Try ISO format
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.warning(f"Could not parse datetime string '{datetime_str}': {e}")
            raise ValueError(f"Could not parse datetime string: {datetime_str}")
    
    raise ValueError(f"Invalid datetime type: {type(datetime_input)}")


def format_date_for_input(date_obj: Union[date, datetime, None]) -> str:
    """
    Format a date object for HTML date input (YYYY-MM-DD)
    
    Args:
        date_obj: date, datetime, or None
        
    Returns:
        Formatted date string or empty string
    """
    if not date_obj:
        return ''
        
    try:
        if isinstance(date_obj, datetime):
            return date_obj.date().strftime('%Y-%m-%d')
        elif isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
        else:
            return str(date_obj)
    except Exception as e:
        logger.warning(f"Could not format date '{date_obj}': {e}")
        return ''


def is_valid_date_string(date_str: str) -> bool:
    """
    Check if a string is a valid date format
    
    Args:
        date_str: String to check
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
        
    try:
        parse_date_string(date_str)
        return True
    except ValueError:
        return False


def is_valid_datetime_string(datetime_str: str) -> bool:
    """
    Check if a string is a valid datetime format
    
    Args:
        datetime_str: String to check
        
    Returns:
        True if valid, False otherwise
    """
    if not datetime_str or not isinstance(datetime_str, str):
        return False
        
    try:
        parse_datetime_string(datetime_str)
        return True
    except ValueError:
        return False
