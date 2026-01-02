"""
Holiday Detection Service.

Provides automatic holiday detection based on timezone/country.
Implements AVAIL-2: Holiday blocking (auto-detect + custom).
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class HolidayService:
    """
    Service for detecting and managing holidays.

    Supports:
    - US holidays (Federal and common observances)
    - Basic international holiday detection
    - Custom holiday management
    """

    # US Federal Holidays (fixed dates)
    US_FIXED_HOLIDAYS = {
        (1, 1): "New Year's Day",
        (7, 4): "Independence Day",
        (11, 11): "Veterans Day",
        (12, 25): "Christmas Day",
    }

    def get_us_holidays(self, year: int) -> List[Dict[str, str]]:
        """
        Get US Federal holidays for a given year.

        Args:
            year: Year to get holidays for

        Returns:
            List of holiday dictionaries with 'date' and 'name' keys
        """
        holidays = []

        # Fixed date holidays
        for (month, day), name in self.US_FIXED_HOLIDAYS.items():
            holidays.append({
                'date': date(year, month, day).strftime('%Y-%m-%d'),
                'name': name,
            })

        # Computed holidays
        # Martin Luther King Jr. Day (3rd Monday in January)
        holidays.append({
            'date': self._get_nth_weekday(year, 1, 0, 3).strftime('%Y-%m-%d'),
            'name': "Martin Luther King Jr. Day",
        })

        # Presidents' Day (3rd Monday in February)
        holidays.append({
            'date': self._get_nth_weekday(year, 2, 0, 3).strftime('%Y-%m-%d'),
            'name': "Presidents' Day",
        })

        # Memorial Day (Last Monday in May)
        holidays.append({
            'date': self._get_last_weekday(year, 5, 0).strftime('%Y-%m-%d'),
            'name': "Memorial Day",
        })

        # Labor Day (1st Monday in September)
        holidays.append({
            'date': self._get_nth_weekday(year, 9, 0, 1).strftime('%Y-%m-%d'),
            'name': "Labor Day",
        })

        # Columbus Day (2nd Monday in October)
        holidays.append({
            'date': self._get_nth_weekday(year, 10, 0, 2).strftime('%Y-%m-%d'),
            'name': "Columbus Day",
        })

        # Thanksgiving (4th Thursday in November)
        holidays.append({
            'date': self._get_nth_weekday(year, 11, 3, 4).strftime('%Y-%m-%d'),
            'name': "Thanksgiving Day",
        })

        return holidays

    def get_holidays_for_timezone(self, timezone_name: str, year: int) -> List[Dict[str, str]]:
        """
        Get holidays for a given timezone.

        Args:
            timezone_name: Timezone name (e.g., "America/New_York")
            year: Year to get holidays for

        Returns:
            List of holiday dictionaries with 'date' and 'name' keys
        """
        # Basic timezone to country mapping
        # This is a simplified implementation - a production system would use a more comprehensive mapping
        if timezone_name.startswith('America/'):
            if 'US' in timezone_name or 'New_York' in timezone_name or 'Chicago' in timezone_name or 'Los_Angeles' in timezone_name or 'Denver' in timezone_name:
                return self.get_us_holidays(year)
            # Could add Canadian, Mexican, etc. holidays here
        elif timezone_name.startswith('Europe/'):
            # Could add European holidays here
            return []
        elif timezone_name.startswith('Asia/'):
            # Could add Asian holidays here
            return []
        elif timezone_name.startswith('Australia/'):
            # Could add Australian holidays here
            return []

        # Default: US holidays
        return self.get_us_holidays(year)

    def get_holiday_dates(
        self,
        timezone_name: str,
        start_date: date,
        end_date: date,
        custom_holidays: List[Dict[str, str]] = None,
    ) -> Set[date]:
        """
        Get set of holiday dates in a date range.

        Args:
            timezone_name: Timezone name for auto-detection
            start_date: Start of date range
            end_date: End of date range
            custom_holidays: Optional list of custom holidays

        Returns:
            Set of holiday dates
        """
        holiday_dates = set()

        # Auto-detected holidays
        for year in range(start_date.year, end_date.year + 1):
            holidays = self.get_holidays_for_timezone(timezone_name, year)
            for holiday in holidays:
                holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
                if start_date <= holiday_date <= end_date:
                    holiday_dates.add(holiday_date)

        # Custom holidays
        if custom_holidays:
            for holiday in custom_holidays:
                holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
                if start_date <= holiday_date <= end_date:
                    holiday_dates.add(holiday_date)

        return holiday_dates

    def is_holiday(
        self,
        check_date: date,
        timezone_name: str,
        custom_holidays: List[Dict[str, str]] = None,
    ) -> bool:
        """
        Check if a date is a holiday.

        Args:
            check_date: Date to check
            timezone_name: Timezone name for auto-detection
            custom_holidays: Optional list of custom holidays

        Returns:
            True if date is a holiday, False otherwise
        """
        holidays = self.get_holiday_dates(
            timezone_name=timezone_name,
            start_date=check_date,
            end_date=check_date,
            custom_holidays=custom_holidays,
        )
        return check_date in holidays

    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """
        Get the nth occurrence of a weekday in a month.

        Args:
            year: Year
            month: Month (1-12)
            weekday: Day of week (0=Monday, 6=Sunday)
            n: Which occurrence (1=first, 2=second, etc.)

        Returns:
            Date of the nth weekday
        """
        # Start with the first day of the month
        current = date(year, month, 1)

        # Find the first occurrence of the target weekday
        while current.weekday() != weekday:
            current = date(year, month, current.day + 1)

        # Add weeks to get to the nth occurrence
        current = date(year, month, current.day + (n - 1) * 7)

        return current

    def _get_last_weekday(self, year: int, month: int, weekday: int) -> date:
        """
        Get the last occurrence of a weekday in a month.

        Args:
            year: Year
            month: Month (1-12)
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            Date of the last weekday
        """
        # Start with the last day of the month
        if month == 12:
            current = date(year, month, 31)
        else:
            current = date(year, month + 1, 1)
            current = date(year, month, current.day - 1)

        # Go backwards to find the target weekday
        while current.weekday() != weekday:
            current = date(year, month, current.day - 1)

        return current
