from django.conf import settings

from .client import Client
from. requesters import Message, Event


class Mailgun:
    def __init__(self, profile):
        self.profile = profile

        self.message = Message(self)
        self.event = Event(self)

    @property
    def profile_settings(self):
        return self.settings["EMAIL_PROFILES"][self.profile]

    @property
    def settings(self):
        return settings.REBEL

    def client(self):
        return Client(self)
