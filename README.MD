# Django Rebel

## Requirements
- Django >= 2.0
- Postgresql

## Installation
```
pip install django-rebel
```

Add `django_rebel` to your INSTALLED_APPS setting.
```
INSTALLED_APPS = (
    ...
    'django_rebel',
)
```

Add Django Rebel settings to your settings file.
```
REBEL = {
    "TEST_MODE": False,
    "SEARCH_FIELDS": [],
    "EMAIL_PROFILES": {
        'MARKETING': {
            'EMAIL': "anyone@example.com",
            'FULL_NAME': 'Anyone',
            "API": {
                "API_KEY": "MAILGUN_API_KEY",
                "DOMAIN": "mg.example.com"
            }
        }
    }
}
```
