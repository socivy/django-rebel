import factory

from django_rebel.models import Mail, MailLabel, MailContent, Event

from tests.models import Owner


class OwnerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Owner


class MailFactory(factory.DjangoModelFactory):
    owner_object = factory.SubFactory(OwnerFactory)

    class Meta:
        model = Mail

    @factory.sequence
    def message_id(u):
        return "message_id_%d" % u


class MailLabelFactory(factory.DjangoModelFactory):
    class Meta:
        model = MailLabel


class MailContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = MailContent


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event
