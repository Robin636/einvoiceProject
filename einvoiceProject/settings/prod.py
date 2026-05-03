from .base import *

CSRF_TRUSTED_ORIGINS=['eiv.edvin.co', 'www.eiv.edvin.co', 'https://eiv.edvin.co']
DEBUG = False
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = ['eiv.edvin.co', '127.0.0.1']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SECURE_SSL_REDIRECT = True  # 27.4.2026

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



