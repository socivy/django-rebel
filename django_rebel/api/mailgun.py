from django_rebel.settings import get_settings, get_profile_settings

from .client import Client
from .requesters import Message, Event


class Mailgun:
    def __init__(self, profile):
        self.profile = profile

        self.message = Message(self)
        self.event = Event(self)

    @property
    def profile_settings(self):
        return get_profile_settings(self.profile)

    @property
    def settings(self):
        return get_settings()

    def client(self):
        return Client(self)
