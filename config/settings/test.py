from os import environ
from .base import *

THIRD_PARTY_APPS = (
    'django_nose',  # for unittest using this package
)

INSTALLED_APPS += THIRD_PARTY_APPS

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': environ.get('DB.', 'kumparan'),
        'USER': environ.get('USER_DB.', 'postgresuser'),
        'PASSWORD': environ.get('PASS_DB.', 'mysecretpass'),
        'HOST': environ.get('HOST_DB.', 'postgres'),
        'PORT': environ.get('PORT_DB.', '5432'),
        'ATOMIC_REQUESTS': True,
    }
}