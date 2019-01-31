from typing import List

from requests.exceptions import ConnectionError

from django.core import mail

from django_rebel.exceptions import RebelAPIError, RebelConnectionError
from django_rebel.models import MailOwner, Mail, MailLabel


class MailSender:
    def __init__(self, profile: str, owners: List[MailOwner], to_mode: str = "to", batch_mode: bool = False):
        self.profile = profile
        self.owners = owners
        self.to_mode = to_mode
        self.batch_mode = batch_mode

    def mailgun(self):
        from django_rebel.api.mailgun import Mailgun

        return Mailgun(self.profile)

    def owner_emails(self):
        return list(self.owner_email_matches().keys())

    def owner_email_matches(self):
        return {owner.get_email(): owner for owner in self.owners}

    def send(self, from_address=None, label: str = None, tags=None, variables=None, fail_silently=True, **kwargs):
        if from_address is None:
            from_address = self.mailgun().profile_settings["EMAIL"]

        if label:
            tags = tags or []
            tags.append(label)

        if self.batch_mode:
            # This is little tricky method for forcing to send mail as batch
            if variables is None:
                variables = {"nobody@example.com": {"no-data": "no"}}

        kwargs.update(
            {
                self.to_mode: self.owner_emails(),
                'from_address': from_address,
                'tags': tags,
                'variables': variables
            }
        )

        try:
            sent_mail_response = self.mailgun().message.send(**kwargs)
        except RebelAPIError as e:
            if fail_silently:
                return False

            raise e
        except ConnectionError:
            raise RebelConnectionError()
        else:
            sent_mails = self._save_mails(from_address, sent_mail_response.message_id(), label, tags)

            # mail.outbox += sent_mails

            return sent_mails

    def _save_mails(self, from_address, message_id, label_slug=None, tags=None):
        mails = []

        if label_slug:
            label, _ = MailLabel.objects.get_or_create(slug=label_slug, defaults={"name": label_slug})
        else:
            label = None

        for owner_email, owner in self.owner_email_matches().items():
            mail = Mail(email_from=from_address,
                        email_to=owner_email,
                        message_id=message_id,
                        profile=self.profile,
                        label=label,
                        tags=tags)

            mail.owner_object = owner

            mails.append(mail)

        created_mails = Mail.objects.bulk_create(mails)

        return created_mails
