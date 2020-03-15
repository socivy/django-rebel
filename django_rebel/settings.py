from django.conf import settings as django_settings


def get_settings():
    return django_settings.REBEL


def get_profile_settings(profile: str):
    return get_settings()["EMAIL_PROFILES"][profile]
