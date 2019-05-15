import logging

import math
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.db import models
from django.template import loader
from django.utils import timezone
from premailer import Premailer

from django_rebel.models import Mail
from django_rebel.services import MailSender


class TemplateMailSender:
    email_profile = "DEFAULT"
    email_label = None
    plain_email_template_path = None
    html_email_template_path = None
    html_email_template_style_path = None
    subject_template_path = None
    tags = None
    from_address = None
    batch_mode = True

    # This field is for filtering owners by sent mails
    send_once = False

    # This is filter field for filtering owners
    send_frequency = 0

    def __init__(self, owners):
        if self.get_subject_template_path() is None or \
                self.get_plain_email_template_path() is None or \
                self.get_email_profile() is None or \
                self.get_email_label() is None:
            raise ValueError("Missing parameters")

        self.owners = owners
        self.variables = self.get_variables()

    @property
    def template_variables(self):
        # Do not calculate variables over and over again,
        # Just cache it!
        if hasattr(self, "_template_variables") is False:
            setattr(self, "_template_variables", self.get_template_variables())

        return self._template_variables

    def get_from_address(self):
        return self.from_address

    def get_subject_template_path(self):
        return self.subject_template_path

    def get_html_email_template_path(self):
        return self.html_email_template_path

    def get_html_email_template_style_path(self):
        return self.html_email_template_style_path

    def get_email_profile(self):
        return self.email_profile

    def get_email_label(self):
        return self.email_label

    def get_send_frequency(self):
        if self.send_once and self.send_frequency:
            raise ValueError("send_once and send_frequency can not set together")

        if self.send_once is True:
            return math.inf

        return self.send_frequency

    def has_html_email(self):
        return self.html_email_template_path is not None

    def get_plain_email_template_path(self):
        return self.plain_email_template_path

    def get_html_email_template_style_content(self):
        if self.get_html_email_template_style_path() is None:
            return None

        abs_style_path = find(self.get_html_email_template_style_path())
        style_content = open(abs_style_path).read()

        return style_content

    def get_html_email_content(self):
        if not self.has_html_email():
            return None

        html_email = loader.render_to_string(self.get_html_email_template_path(), self.template_variables)

        html_email = Premailer(html_email, cssutils_logging_level=logging.FATAL).transform()

        return html_email

    def get_plain_email_content(self):
        plain_email = loader.render_to_string(self.get_plain_email_template_path(), self.template_variables)

        return plain_email

    def get_subject_content(self):
        subject = loader.render_to_string(self.get_subject_template_path(), self.template_variables)

        return subject

    def get_template_variables(self):
        return {
            'style_content': self.get_html_email_template_style_content()
        }

    def get_tags(self):
        return self.tags

    def get_variables(self):
        return {}

    def get_inline_files(self):
        return []

    def get_available_owners_by_frequency(self):
        # This function is filtering owners by sent mails

        send_frequency = self.get_send_frequency()

        if send_frequency == 0:
            return self.owners

        send_once = send_frequency == math.inf

        sent_mails = self.get_sent_mails()

        if send_once is False:
            time_limit = timezone.now() - timezone.timedelta(seconds=send_frequency)

            sent_mails = sent_mails.filter(created_at__gte=time_limit)

        sent_mail_owners = [sent_mail.owner_object for sent_mail in sent_mails.all()]

        def is_available(owner):
            for sent_owner in sent_mail_owners:
                if sent_owner == owner:
                    return False

            return True

        available_owners = list(filter(is_available, self.owners))

        return available_owners

    def get_available_owners(self, ):
        owners = self.get_available_owners_by_frequency()

        owners = self.validate_available_owners(owners)

        return owners

    def validate_available_owners(self, owners):
        # This method is filtering for available owners
        return owners

    def send(self, force=False, fail_silently=False):
        if force:
            owners = self.owners
        else:
            # If there is no one to send,
            # Then return False
            owners = self.get_available_owners()

            if len(owners) == 0:
                return False

        self.before_send(owners)

        mails = self.perform_send(owners, fail_silently)

        self.after_send(mails)

        return mails

    def perform_send(self, owners, fail_silently=False):
        mail_sender = MailSender(self.get_email_profile(), owners=owners, batch_mode=self.batch_mode)

        mails = mail_sender.send(from_address=self.get_from_address(),
                                 label=self.get_email_label(),
                                 tags=self.get_tags(),
                                 subject=self.get_subject_content(),
                                 html=self.get_html_email_content(),
                                 text=self.get_plain_email_content(),
                                 files=self.get_inline_files(),
                                 variables=self.variables,
                                 fail_silently=fail_silently)

        return mails

    def after_send(self, mails):
        """
        This method is helping for staging sending scenario
        """

    def before_send(self, owners):
        """
        This method is helping for staging sending scenario
        """

    def get_sent_mails(self):
        owner_query = None

        for owner in self.owners:
            owner_type = ContentType.objects.get(app_label=owner._meta.app_label,
                                                 model=owner._meta.model_name)

            if owner_query is None:
                owner_query = models.Q(owner_type=owner_type, owner_id=owner.id)
            else:
                owner_query = owner_query | models.Q(owner_type=owner_type, owner_id=owner.id)

        return Mail.objects.filter(owner_query).filter(label__slug=self.get_email_label())
