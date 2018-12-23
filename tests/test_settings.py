import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True

SECRET_KEY = 'secretkey'

ROOT_URLCONF = 'tests.test_urls'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'django_rebel',
    'tests',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'django_rebel',
        'USER': 'django_rebel',
        'PASSWORD': 'django_rebel',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

SITE_ID = 1

STATIC_URL = '/static/'

REBEL = {
    "TEST_MODE": True,
    "SEARCH_FIELDS": [],
    "EMAIL_PROFILES": {
        'MARKETING': {
            'EMAIL': "anyone@example.com",
            'FULL_NAME': 'Example Name',
            "API": {
                "API_KEY": "",
                "DOMAIN": "mg.example.com"
            }
        }
    }
}
