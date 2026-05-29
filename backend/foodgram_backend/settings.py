import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', default=get_random_secret_key())

DEBUG = os.getenv('DEBUG', default='False') == 'True'

_raw_hosts = os.getenv('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'django_filters',

    'users.apps.UsersConfig',
    'api.apps.ApiConfig',
    'recipes.apps.RecipesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # должен быть выше CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'foodgram_backend.wsgi.application'

# --- Database ----------------------------------------------------------------

USE_SQLITE = os.getenv('USE_SQLITE', default='False') == 'True'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'django'),
            'USER': os.getenv('POSTGRES_USER', 'django'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', 5432),
        }
    }

# --- Auth --------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

# --- REST Framework ----------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'api.paginator.RecipeBookPagination',
    'PAGE_SIZE': 6,

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),

    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/day',
        'user': '2000/day',
    },
}

# --- Djoser ------------------------------------------------------------------

DJOSER = {
    'LOGIN_FIELD': 'email',
    'HIDE_USERS': False,
    'SERIALIZERS': {
        'user': 'api.serializers.UsersSerializer',
        'current_user': 'api.serializers.UsersSerializer',
    },
    'PERMISSIONS': {
        'user': ('rest_framework.permissions.IsAuthenticated',),
        'user_list': ('rest_framework.permissions.AllowAny',),
    },
}

# --- CORS --------------------------------------------------------------------

_raw_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _raw_cors.split(',') if o.strip()]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# --- Security ----------------------------------------------------------------

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# --- Internationalization ----------------------------------------------------

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --- Static / Media ----------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv('STATIC_ROOT', str(BASE_DIR / 'collected_static')))

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Misc --------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
