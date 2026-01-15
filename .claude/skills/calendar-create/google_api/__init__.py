"""
Google API Manager Package for Calendar Create

This package provides managers for Google Calendar API services with write access.
"""

from .base import GoogleAPIManager
from .calendar import GoogleCalendarAPIManager

__all__ = ['GoogleAPIManager', 'GoogleCalendarAPIManager']
