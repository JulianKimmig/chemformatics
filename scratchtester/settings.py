from djangobase.settings import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG.read(os.path.join(BASE_DIR, "config.json"))


SECRET_KEY = CONFIG.get(
    "Instance",
    "key",
    default="".join(
        random.SystemRandom().choice(
            "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
        )
        for i in range(50)
    ),
)


DEBUG = CONFIG.get("Instance", "debug", default=DEBUG)

ALLOWED_HOSTS = CONFIG.get("Instance", "allowed-hosts", default=ALLOWED_HOSTS)

INSTALLED_APPS = INSTALLED_APPS + [
    app_data.get("install", app_name)
    for app_name, app_data in CONFIG.get("Apps", default={}).items()
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

MEDIA_ROOT = os.path.join(BASE_DIR, "data")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, app_name, "static")
    for app_name, app_data in CONFIG.get("Apps", default={}).items()
]

CONFIG.save()
