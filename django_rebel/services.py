import logging

from premailer import Premailer
from requests.exceptions import ConnectionError

from django_rebel.exceptions import RebelAPIError, RebelConnectionError
from django_rebel.models import MailOwner, Mail, MailLabel


class PreparedMail:
    def __init__(self, subject: str, profile: str = "DEFAULT", from_address: str = None, to_mode: str = "to",
                 batch_mode: bool = True, label: str = None, tags: list = None, text=None, html=None,
                 variables: dict = None, inlines: list = None, attachments: list = None):
        self.profile = profile

        # Sender Options
        self.to_mode = to_mode
        self.batch_mode = batch_mode
        self.label = label
        self.tags = tags
        self.from_address = from_address or self.mailgun().profile_settings['EMAIL']

        self.receivers = []

        # Mail Content Options
        self.subject = subject
        self.text = text
        self.html = html
        self.inlines = inlines
        self.attachments = attachments
        self.variables = variables

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, value):
        if value:
            value = Premailer(value, cssutils_logging_level=logging.FATAL).transform()

        self._html = value

    def mailgun(self):
        from django_rebel.api.mailgun import Mailgun

        return Mailgun(self.profile)

    def add_receiver(self, owner: MailOwner = None, email_to: str = None):
        assert owner is not None or email_to is not None, "owner or email_to is required"

        email_to = email_to or owner.get_email()

        self.receivers.append({
            'email_to': email_to,
            'owner': owner
        })

        return self

    @property
    def receiver_emails(self):
        return [receiver['email_to'] for receiver in self.receivers]

    def send(self, fail_silently=True, **kwargs):
        if self.batch_mode:
            # This is little tricky method for forcing to send mail as batch
            if self.variables is None:
                self.variables = {"nobody@example.com": {"no-data": "no"}}

        kwargs.update(
            {
                self.to_mode: self.receiver_emails,
                'from_address': self.from_address,
                'tags': self.tags,

                'subject': self.subject,
                'html': self.html,
                'text': self.text,
                'variables': self.variables,
                'inlines': self.inlines,
                'attachments': self.attachments
            }
        )

        try:
            sent_mail_response = self.mailgun().message.send(**kwargs)
        except RebelAPIError as e:
            if fail_silently:
                return [], False

            raise e
        except ConnectionError:
            raise RebelConnectionError()
        else:
            sent_mails = self._save_mails(sent_mail_response.message_id())

            return sent_mails, True

    def _save_mails(self, message_id):
        mails = []

        if self.label:
            label, _ = MailLabel.objects.get_or_create(slug=self.label, defaults={"name": self.label})
        else:
            label = None

        for receiver in self.receivers:
            mail = Mail(email_from=self.from_address,
                        email_to=receiver["email_to"],
                        message_id=message_id,
                        profile=self.profile,
                        label=label,
                        tags=self.tags)

            mail.owner_object = receiver["owner"]

            mails.append(mail)

        created_mails = Mail.objects.bulk_create(mails)

        return created_mails
