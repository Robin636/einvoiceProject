from .base import *

DEBUG = True
CSRF_TRUSTED_ORIGINS=['http://127.0.0.1']
ALLOWED_HOSTS = ['*']
SECRET_KEY = 'django-insecure-*1(u(7m-)be_c(u@7ul-lxw8^zuv)9hk-$#s7*&_en231a_cum'


DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }

}


