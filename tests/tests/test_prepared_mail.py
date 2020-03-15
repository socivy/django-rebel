import re

from django.test import TestCase
from httpretty import httpretty

from django_rebel.exceptions import RebelAPIError
from django_rebel.services import PreparedMail


class PreparedMailTestCase(TestCase):
    def test_fail_silently(self):
        httpretty.enable()

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body="{}",
            status=400
        )

        prepared_mail = PreparedMail(subject="foo")

        _, status = prepared_mail.send(fail_silently=True)

        self.assertFalse(status)

        httpretty.register_uri(
            httpretty.POST,
            re.compile(r'.*'),
            body="{}",
            status=400
        )

        with self.assertRaises(RebelAPIError):
            prepared_mail.send(fail_silently=False)
