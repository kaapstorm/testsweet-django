SECRET_KEY = 'not-a-secret'
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
]
USE_TZ = True
