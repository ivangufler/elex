"""
Django settings for elex project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from . import secret

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory where Django static files are collected
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL where static files will be served
STATIC_URL = '/static/'

# Vue project location
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Vue assets directory (assetsDir)
STATICFILES_DIRS = [
    os.path.join(FRONTEND_DIR, 'dist/static'),
]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secret.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'elections',
    'rest_framework',
    'corsheaders',
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ONLY FOR DEVELOPMENT
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = False
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000"
    ]
    CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'elex.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'elections/templates',
            os.path.join(FRONTEND_DIR, 'dist'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'elex.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.azuread_tenant.AzureADTenantOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = secret.OAUTH2_KEY
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = secret.OAUTH2_SECRET
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = secret.OAUTH2_TENANT
SOCIAL_AUTH_AZUREAD_OAUTH2_RESOURCE = 'https://graph.microsoft.com/'

LOGIN_REDIRECT_URL = secret.LOGIN_REDIRECT
LOGOUT_REDIRECT_URL = secret.LOGOUT_REDIRECT
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# E-Mail
DEFAULT_FROM_EMAIL = secret.FROM_EMAIL
EMAIL_HOST = secret.EMAIL_HOST
EMAIL_PORT = secret.EMAIL_PORT
EMAIL_HOST_USER = secret.EMAIL_USER
EMAIL_HOST_PASSWORD = secret.EMAIL_PASSWORD
EMAIL_USE_SSL = True

# E-Mail Templates
EMAIL_TEMPLATE_NEW = 'election_new_de.html'
EMAIL_TEMPLATE_REMINDER = 'election_reminder_de.html'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('ELEX_DB_NAME'),
        'USER': os.getenv('ELEX_DB_USER'),
        'PASSWORD': os.getenv('ELEX_DB_PASSWORD'),
        'HOST': os.getenv('ELEX_DB_HOST'),
        'PORT': os.getenv('ELEX_DB_PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True