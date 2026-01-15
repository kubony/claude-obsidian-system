"""
Google API Manager Package for Calendar

This package provides managers for Google Calendar API services.
"""

from .base import GoogleAPIManager
from .calendar import GoogleCalendarAPIManager

__all__ = ['GoogleAPIManager', 'GoogleCalendarAPIManager']
