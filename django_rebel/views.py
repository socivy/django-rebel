import json

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from django_rebel.api.constants import EVENT_TYPES
from django_rebel.models import Mail, MailContent, Event


class MailContentView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        mail_id = kwargs.get("mail_id")

        if mail_id is None:
            raise Http404("Not found")

        try:
            mail = Mail.objects.get(id=mail_id)
        except Mail.DoesNotExist:
            raise Http404("Not found")

        if not hasattr(mail, "content"):
            raise Http404("No content")

        return HttpResponse(content=mail.content.body_html)


@method_decorator(csrf_exempt, name='dispatch')
class EventView(View):
    def post(self, request, *args, **kwargs):
        raw_data = request.body

        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            raise Http404("Content is not valid")

        event_data = data["event-data"]

        # If there is no message area,
        # Then we could not track mail status
        # Because of that, return 404 error
        if "message" not in event_data.keys():
            raise Http404("Message area is not defined")

        message_headers = event_data["message"]["headers"]

        message_id = message_headers["message-id"]
        recipient = event_data["recipient"]

        try:
            mail = Mail.objects.get(message_id=message_id, email_to=recipient)
        except Mail.DoesNotExist:
            return Http404("Mail not found")

        storage = event_data.get("storage", None)

        if not hasattr(mail, "content") and storage:
            mail.storage_url = storage["url"]
            mail.save()

            self._generate_content(mail)

        self._generate_event(event_data, mail)

        return HttpResponse(content="ok")

    def _generate_event(self, event_data, mail):
        event_type = event_data["event"]

        event = Event(mail=mail, name=event_type)

        if event_type == EVENT_TYPES.CLICKED:
            event.extra_data = {
                "url": event_data["url"]
            }

        event.save()

        event_field = "has_%s" % event_type.lower()
        setattr(mail, event_field, True)
        mail.save(update_fields=[event_field])

    def _generate_content(self, mail):
        storage_data = mail.get_storage()

        MailContent.objects.create(
            mail=mail,
            subject=storage_data["subject"],
            body_text=storage_data["stripped-text"],
            body_html=storage_data["stripped-html"],
            body_plain=storage_data["body-plain"]
        )
