"""
Google Calendar API Manager with Write Access

This module provides a manager for Google Calendar API operations including
event creation, modification, and deletion.
"""

from .base import GoogleAPIManager
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
import uuid

class GoogleCalendarAPIManager(GoogleAPIManager):
    """
    Manager for Google Calendar API operations with full read/write access.

    Provides methods for listing, creating, updating, and deleting calendar events.
    """

    # Full access scope (read + write)
    SCOPES = ['https://www.googleapis.com/auth/calendar']
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

    def get_event(self, event_id: str) -> Dict:
        """Get a single event by ID."""
        return self.service.events().get(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        create_meet: bool = False,
        send_updates: bool = True
    ) -> Dict:
        """
        Create a new calendar event.

        Args:
            summary: Event title.
            start: Event start time.
            end: Event end time.
            location: Event location (optional).
            description: Event description (optional).
            attendees: List of attendee email addresses (optional).
            create_meet: Whether to create a Google Meet link.
            send_updates: Whether to send email notifications to attendees.

        Returns:
            Created event dictionary.
        """
        event = {
            'summary': summary,
            'start': {
                'dateTime': self._to_iso(start),
                'timeZone': self.TIMEZONE
            },
            'end': {
                'dateTime': self._to_iso(end),
                'timeZone': self.TIMEZONE
            },
        }

        if location:
            event['location'] = location

        if description:
            event['description'] = description

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        if create_meet:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }

        return self.service.events().insert(
            calendarId=self.calendar_id,
            body=event,
            conferenceDataVersion=1 if create_meet else 0,
            sendUpdates='all' if (send_updates and attendees) else 'none'
        ).execute()

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        send_updates: bool = True
    ) -> Dict:
        """
        Update an existing calendar event.

        Args:
            event_id: ID of the event to update.
            summary: New event title (optional).
            start: New start time (optional).
            end: New end time (optional).
            location: New location (optional).
            description: New description (optional).
            attendees: New list of attendees (optional, replaces existing).
            send_updates: Whether to send email notifications.

        Returns:
            Updated event dictionary.
        """
        # Get existing event
        event = self.get_event(event_id)

        # Update fields
        if summary is not None:
            event['summary'] = summary

        if start is not None:
            event['start'] = {
                'dateTime': self._to_iso(start),
                'timeZone': self.TIMEZONE
            }

        if end is not None:
            event['end'] = {
                'dateTime': self._to_iso(end),
                'timeZone': self.TIMEZONE
            }

        if location is not None:
            event['location'] = location

        if description is not None:
            event['description'] = description

        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]

        return self.service.events().update(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates='all' if send_updates else 'none'
        ).execute()

    def delete_event(self, event_id: str, send_updates: bool = True) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: ID of the event to delete.
            send_updates: Whether to send cancellation emails.

        Returns:
            True if successful.
        """
        self.service.events().delete(
            calendarId=self.calendar_id,
            eventId=event_id,
            sendUpdates='all' if send_updates else 'none'
        ).execute()
        return True

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
            query: Text to search for.
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
        """Format an event for display."""
        start = event.get('start', {})
        end = event.get('end', {})

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
