import json
import re
import urllib
from urllib.parse import urlparse

import requests
import httpretty

from django.test import TestCase

from django_rebel.exceptions import RebelConnectionError, RebelAPIError
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

        httpretty.enable()

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body="{}",
            status=400
        )

        status = mail_sender.send(fail_silently=True)

        self.assertFalse(status)

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body="{}",
            status=400
        )

        with self.assertRaises(RebelAPIError):
            mail_sender.send(fail_silently=False)

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

    def test_connection_error(self):
        owner_1 = OwnerFactory.create()

        mail_sender = TestMailSender(owners=[owner_1])

        httpretty.enable()

        def connection_error(*args):
            raise requests.ConnectionError()

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body=connection_error,
            status=400
        )

        with self.assertRaises(RebelConnectionError):
            mail_sender.send(fail_silently=True)

    def test_send_once(self):
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

        def second_request(request, uri, response_headers):
            content = urllib.parse.parse_qs(request.body)

            self.assertTrue("to" in content)

            return [400, response_headers, "{}"]

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body=second_request
        )

        mails = mail_sender.send()

        self.assertFalse(mails)
        self.assertEqual(Mail.objects.count(), 1)
