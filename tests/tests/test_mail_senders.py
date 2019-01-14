from django.test import TestCase

from django_rebel.mail_senders import TemplateMailSender

from tests.factories import MailFactory, OwnerFactory, MailLabelFactory


class TestMailSender(TemplateMailSender):
    email_label = "test"
    subject_template_path = "foo"
    plain_email_template_path = "foo"
    send_once = True


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
