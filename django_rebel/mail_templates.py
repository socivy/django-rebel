import math
from typing import List

from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.db import models
from django.template import loader
from django.utils import timezone

from django_rebel.models import Mail, MailOwner
from django_rebel.services import PreparedMail
from django_rebel.utils import cached_property


class DjangoMailTemplate:
    email_profile = "DEFAULT"
    email_label = None
    plain_email_template_path = None
    html_email_template_path = None
    html_email_template_style_path = None
    subject_template_path = None
    tags = None
    from_address = None
    batch_mode = True

    # This field is for filtering owner by sent mails
    send_once = False

    # This is filter field for filtering owner
    send_frequency = 0

    def __init__(self, owner):
        if self.get_subject_template_path() is None or \
                self.get_plain_email_template_path() is None or \
                self.get_email_profile() is None or \
                self.get_email_label() is None:
            raise ValueError("Missing Mail Sender parameters")

        self.owner: MailOwner = owner

    @cached_property
    def template_variables(self) -> dict:
        return self.get_template_variables()

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

    def get_inline_files(self):
        return []

    def prepared_mail_receiver(self, mail_sender):
        mail_sender.add_receiver(owner=self.owner, email_to=self.owner.get_email())

    def is_owner_available_by_frequency(self):
        # This function is filtering owner by sent mails

        send_frequency = self.get_send_frequency()

        if send_frequency == 0:
            return True

        send_once = send_frequency == math.inf

        sent_mails = self.get_sent_mails()

        if send_once is False:
            time_limit = timezone.now() - timezone.timedelta(seconds=send_frequency)

            sent_mails = sent_mails.filter(created_at__gte=time_limit)

        return not sent_mails.exists()

    def is_owner_available(self, force=False):
        if force:
            return True

        if self.is_owner_available_by_frequency() is False:
            return False

        if self.validate_owner() is False:
            return False

        return True

    def validate_owner(self):
        # This method is filtering for available owner
        return True

    def send(self, force=False, fail_silently=False, template_variables=None):
        self.template_variables.update(template_variables or {})

        # If there is no one to send,
        # Then return False
        if self.is_owner_available(force=force) is False:
            return False

        self.before_send(self.owner)

        mails, status = self.perform_send(fail_silently)

        if status is False:
            return False

        mail = mails[0]

        self.after_send(mail)

        return mail

    def perform_send(self, fail_silently=False):
        mail_sender = PreparedMail(profile=self.get_email_profile(),
                                   from_address=self.get_from_address(),
                                   label=self.get_email_label(),
                                   tags=self.get_tags(),
                                   subject=self.get_subject_content(),
                                   html=self.get_html_email_content(),
                                   text=self.get_plain_email_content(),
                                   inlines=self.get_inline_files())

        self.prepared_mail_receiver(mail_sender)

        mails = mail_sender.send(fail_silently=fail_silently)

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
        owner_type = ContentType.objects.get(app_label=self.owner._meta.app_label,
                                             model=self.owner._meta.model_name)

        owner_query = models.Q(owner_type=owner_type, owner_id=self.owner.id)

        return Mail.objects.filter(owner_query).filter(label__slug=self.get_email_label())


class BatchTemplateMailSender(DjangoMailTemplate):
    def __init__(self, owners):
        if self.get_subject_template_path() is None or \
                self.get_plain_email_template_path() is None or \
                self.get_email_profile() is None or \
                self.get_email_label() is None:
            raise ValueError("Missing Mail Sender parameters")

        self.owners: List[models.Model] = owners

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

    def get_available_owners_by_frequency(self):
        # This function is filtering owner by sent mails

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

    def get_available_owners(self, force):
        if force:
            return self.owner

        owners = self.get_available_owners_by_frequency()

        owners = self.validate_available_owners(owners)

        return owners

    def validate_available_owners(self, owners):
        # This method is filtering for available owner
        return owners

    def send(self, force=False, fail_silently=False, variables=None, template_variables=None):
        # If there is no one to send,
        # Then return False
        owners = self.get_available_owners(force=force)

        if len(owners) == 0:
            return False

        self.before_send(owners)

        mails = self.perform_send(owners, fail_silently, variables, template_variables)

        self.after_send(mails)

        return mails
