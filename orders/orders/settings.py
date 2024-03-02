import os
import sentry_sdk
from dotenv import load_dotenv
from pathlib import Path
from sentry_sdk.integrations.django import DjangoIntegration

load_dotenv()

s_dsn = os.environ["SENTRY_DSN"]

sentry_sdk.init(
    dsn=s_dsn,
    integrations=[DjangoIntegration(
        transaction_style='url',
        middleware_spans=True,
        signals_spans=False,
        cache_spans=False,
    )],
    enable_tracing=True,
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g9)m3*oq1tzt$_i2ph1x%ya21hk@lek7y4^408!%d=bc(8bv1b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

STATIC_ROOT = BASE_DIR / "staticfiles"

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'localhost']

# Application definition

INSTALLED_APPS = [
    'social_django',
    'jet.dashboard',
    'jet',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_celery_results',
    'rest_framework',
    'rest_framework.authtoken',
    'django_rest_passwordreset',

    'backend',

    'drf_spectacular',
    'drf_spectacular_sidecar',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'orders.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'backend', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]
TEMPLATES[0]['OPTIONS']['debug'] = True
WSGI_APPLICATION = 'orders.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ["DB_NAME"],
        'HOST': os.environ["DB_HOST"],
        'PORT': os.environ["DB_PORT"],
        'USER': os.environ["DB_USER"],
        'PASSWORD': os.environ["DB_PASSWORD"]
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'backend.User'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
EMAIL_PORT = os.environ["EMAIL_PORT"]
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
SERVER_EMAIL = EMAIL_HOST_USER

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '2/second',
        'user': '10/second'
    }
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.vk.VKOAuth2',
    # Add other backends as needed
    'django.contrib.auth.backends.ModelBackend',  # default Django authentication backend
)


SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ["GOOGLE_AUTH_KEY"]
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ["GOOGLE_AUTH_SECRET"]
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://example.com/'

SOCIAL_AUTH_FACEBOOK_KEY = os.environ["FACEBOOK_AUTH_KEY"]
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ["FACEBOOK_AUTH_SECRET"]
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI = 'https://example.com/'

SOCIAL_AUTH_VK_OAUTH2_KEY = os.environ["VK_AUTH_KEY"]
SOCIAL_AUTH_VK_OAUTH2_SECRET = os.environ["VK_AUTH_SECRET"]
SOCIAL_AUTH_VK_OAUTH2_REDIRECT_URI = 'https://example.com/'

SPECTACULAR_SETTINGS = {
    'TITLE': 'Orders backend',
    'DESCRIPTION': 'The application provides methods to work with shop',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_CONNECTION_TIMEOUT = 10  # or a higher value
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')
