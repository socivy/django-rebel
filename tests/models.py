from django.db import models

from django_rebel.models import MailOwner


class Owner(MailOwner):
    email = models.EmailField()

    def get_email(self):
        return self.email

    def get_admin_view_link(self):
        return self.pk
