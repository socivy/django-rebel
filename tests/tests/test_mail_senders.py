import json

import re
from django.test import TestCase

import httpretty

from django_rebel.mail_senders import TemplateMailSender
from django_rebel.models import Mail

from tests.factories import MailFactory, OwnerFactory, MailLabelFactory


class TestMailSender(TemplateMailSender):
    email_label = "test"
    subject_template_path = "subject.txt"
    plain_email_template_path = "content.html"
    send_once = True

    def get_subject_content(self):
        return "Subject"

    def get_plain_email_content(self):
        return "Content"


class TemplateMailSenderTestCase(TestCase):
    def test_get_available_owners(self):
        owner_1 = OwnerFactory.create()

        mail_sender = TestMailSender(owners=[owner_1])
        self.assertListEqual([owner_1], mail_sender.get_available_owners())

        mail_label = MailLabelFactory.create(slug=mail_sender.get_email_label())

        MailFactory.create(label=mail_label)
        self.assertListEqual([owner_1], mail_sender.get_available_owners())

        MailFactory.create(owner_object=owner_1, label=mail_label)

        self.assertListEqual([], mail_sender.get_available_owners())

        mail_sender.send_once = False
        self.assertListEqual([owner_1], mail_sender.get_available_owners())

    def test_fail_silently(self):
        owner_1 = OwnerFactory.create()

        mail_sender = TestMailSender(owners=[owner_1])

        status = mail_sender.send(fail_silently=True)

        self.assertFalse(status)

    def test_send_mail(self):
        httpretty.enable()

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body=json.dumps({"id": "foo"})
        )

        owner_1 = OwnerFactory.create()

        mail_sender = TestMailSender(owners=[owner_1])

        mails = mail_sender.send()

        self.assertEqual(Mail.objects.count(), 1)
        self.assertEqual(mails.__len__(), 1)
