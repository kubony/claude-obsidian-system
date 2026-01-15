"""
Google Calendar API Manager

This module provides a manager for Google Calendar API operations.
"""

from .base import GoogleAPIManager
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

class GoogleCalendarAPIManager(GoogleAPIManager):
    """
    Manager for Google Calendar API operations.

    Provides methods for listing, creating, updating, and deleting calendar events.
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    TIMEZONE = 'Asia/Seoul'

    def __init__(self, key_file: str, calendar_id: str = 'primary'):
        """
        Initialize the Calendar API Manager.

        Args:
            key_file (str): Path to the service account key file.
            calendar_id (str): Calendar ID to operate on. Defaults to 'primary'.
        """
        super().__init__(key_file, self.SCOPES)
        self.service = self.build_service('calendar', 'v3')
        self.calendar_id = calendar_id
        self.tz = pytz.timezone(self.TIMEZONE)

    def _to_iso(self, dt: datetime) -> str:
        """Convert datetime to ISO format with timezone."""
        if dt.tzinfo is None:
            dt = self.tz.localize(dt)
        return dt.isoformat()

    def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        max_results: int = 100,
        query: Optional[str] = None
    ) -> List[Dict]:
        """
        List events within a time range.

        Args:
            time_min: Start of time range.
            time_max: End of time range.
            max_results: Maximum number of events to return.
            query: Optional text search query.

        Returns:
            List of event dictionaries.
        """
        params = {
            'calendarId': self.calendar_id,
            'timeMin': self._to_iso(time_min),
            'timeMax': self._to_iso(time_max),
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': max_results,
        }
        if query:
            params['q'] = query

        events_result = self.service.events().list(**params).execute()
        return events_result.get('items', [])

    def get_today_events(self) -> List[Dict]:
        """Get events for today."""
        now = datetime.now(self.tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return self.list_events(today_start, today_end)

    def get_week_events(self) -> List[Dict]:
        """Get events for the current week (Monday to Sunday)."""
        now = datetime.now(self.tz)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        return self.list_events(start_of_week, end_of_week)

    def get_event(self, event_id: str) -> Dict:
        """
        Get a single event by ID.

        Args:
            event_id: The event ID.

        Returns:
            Event dictionary.
        """
        return self.service.events().get(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()

    def search_events(
        self,
        query: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search events by text query.

        Args:
            query: Text to search for in event titles.
            time_min: Optional start of time range.
            time_max: Optional end of time range.
            max_results: Maximum number of events to return.

        Returns:
            List of matching events.
        """
        if time_min is None:
            time_min = datetime.now(self.tz) - timedelta(days=365)
        if time_max is None:
            time_max = datetime.now(self.tz) + timedelta(days=365)

        return self.list_events(time_min, time_max, max_results, query=query)

    @staticmethod
    def format_event(event: Dict) -> Dict:
        """
        Format an event for display.

        Args:
            event: Raw event dictionary from API.

        Returns:
            Formatted event dictionary with standardized fields.
        """
        start = event.get('start', {})
        end = event.get('end', {})

        # Handle all-day events vs timed events
        start_time = start.get('dateTime', start.get('date', ''))
        end_time = end.get('dateTime', end.get('date', ''))

        attendees = []
        for attendee in event.get('attendees', []):
            email = attendee.get('email', '')
            if email and not email.endswith('calendar.google.com'):
                attendees.append(email)

        return {
            'id': event.get('id', ''),
            'summary': event.get('summary', '(제목 없음)'),
            'start': start_time,
            'end': end_time,
            'location': event.get('location', ''),
            'description': event.get('description', ''),
            'attendees': attendees,
            'html_link': event.get('htmlLink', ''),
            'hangout_link': event.get('hangoutLink', ''),
        }
