"""
Event Integrations Package - Real event data from external APIs
"""

from .base_event_provider import BaseEventProvider, EventData
from .eventbrite_provider import EventbriteProvider

__all__ = ['BaseEventProvider', 'EventData', 'EventbriteProvider']