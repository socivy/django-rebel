from django.urls import path

from django_rebel.views import EventView, MailContentView

app_name = "rebel"

urlpatterns = [
    path("event", EventView.as_view(), name="event"),
    path("content/<str:mail_id>", MailContentView.as_view(), name="content"),
]
