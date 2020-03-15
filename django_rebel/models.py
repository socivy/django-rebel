import requests
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.urls import reverse

from django_rebel.api.constants import EVENT_TYPES


class TimeBasedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class MailLabel(TimeBasedModel):
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)

    def __str__(self):
        return self.name


class MailQuerySet(models.QuerySet):
    use_in_migrations = True

    def with_event_status(self):
        return self.annotate(
            calculated_has_opened=models.Exists(
                Event.objects.filter(mail=models.OuterRef("id"), name=EVENT_TYPES.OPENED)),
            calculated_has_delivered=models.Exists(
                Event.objects.filter(mail=models.OuterRef("id"), name=EVENT_TYPES.DELIVERED)),
            calculated_has_clicked=models.Exists(
                Event.objects.filter(mail=models.OuterRef("id"), name=EVENT_TYPES.CLICKED)),
        )


class MailManager(models.Manager.from_queryset(MailQuerySet)):
    use_in_migrations = True


class Mail(TimeBasedModel):
    email_from = models.CharField(max_length=256, db_index=True)
    email_to = models.CharField(max_length=256, db_index=True)
    message_id = models.CharField(max_length=256)

    profile = models.CharField(max_length=32)

    storage_url = models.URLField(null=True, blank=True)

    owner_type = models.ForeignKey(ContentType,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)
    owner_id = models.PositiveIntegerField(null=True, blank=True)
    owner_object = GenericForeignKey('owner_type', 'owner_id')

    label = models.ForeignKey(MailLabel, null=True, blank=True, on_delete=models.CASCADE)

    tags = ArrayField(
        models.CharField(max_length=64), null=True, blank=True,
        db_index=True
    )

    has_accepted = models.BooleanField(default=False)
    has_rejected = models.BooleanField(default=False)
    has_delivered = models.BooleanField(default=False)
    has_failed = models.BooleanField(default=False)
    has_opened = models.BooleanField(default=False)
    has_clicked = models.BooleanField(default=False)
    has_unsubscribed = models.BooleanField(default=False)
    has_complained = models.BooleanField(default=False)
    has_stored = models.BooleanField(default=False)

    objects = MailManager()

    class Meta:
        unique_together = ("email_to", "message_id")

    def get_storage(self):
        profile_settings = settings.REBEL["EMAIL_PROFILES"][self.profile]

        auth = ("api", profile_settings["API"]["API_KEY"])

        req = requests.get(self.storage_url, auth=auth)

        return req.json()

    def __str__(self):
        return str(self.id)


class Event(TimeBasedModel):
    mail = models.ForeignKey(Mail, related_name="events", on_delete=models.CASCADE)

    EVENT_NAMES = (
        (EVENT_TYPES.ACCEPTED, EVENT_TYPES.ACCEPTED),
        (EVENT_TYPES.CLICKED, EVENT_TYPES.CLICKED),
        (EVENT_TYPES.COMPLAINED, EVENT_TYPES.COMPLAINED),
        (EVENT_TYPES.DELIVERED, EVENT_TYPES.DELIVERED),
        (EVENT_TYPES.FAILED, EVENT_TYPES.FAILED),
        (EVENT_TYPES.OPENED, EVENT_TYPES.OPENED),
        (EVENT_TYPES.REFECTED, EVENT_TYPES.REFECTED),
        (EVENT_TYPES.UNSUBSCRIBED, EVENT_TYPES.UNSUBSCRIBED),
    )

    name = models.CharField(max_length=32, choices=EVENT_NAMES)

    extra_data = JSONField(null=True, blank=True)

    def __str__(self):
        return "%s Event: %s" % (self.mail.__str__(), self.name)


class MailContent(TimeBasedModel):
    mail = models.OneToOneField(Mail, related_name="content", on_delete=models.CASCADE)

    subject = models.CharField(max_length=512, null=True, blank=True)
    body_text = models.TextField(null=True, blank=True)
    body_html = models.TextField(null=True, blank=True)
    body_plain = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.subject

    def get_content_url(self):
        return reverse("rebel:content", kwargs={"mail_id": self.mail_id})


class MailOwner(models.Model):
    def get_email(self):
        raise NotImplementedError()

    def get_admin_view_link(self):
        url = reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])

        return url

    class Meta:
        abstract = True
