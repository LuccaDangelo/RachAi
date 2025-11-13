
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):
        return False

try:
    import whitenoise  # noqa: F401
except ImportError:  # pragma: no cover - optional dependency
    WHITENOISE_INSTALLED = False
else:
    WHITENOISE_INSTALLED = True


BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


TARGET_ENV = os.getenv('TARGET_ENV', 'development')
IS_PRODUCTION = TARGET_ENV.lower().startswith('prod')


if not IS_PRODUCTION:
    SECRET_KEY = 'django-insecure-sua-chave-de-desenvolvimento-aqui'
    DEBUG = True
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

else:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ImproperlyConfigured("A SECRET_KEY não foi definida no ambiente de produção!")

    DEBUG = os.getenv('DEBUG', '0').lower() in ['true', 't', '1']
    
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split()
    if not ALLOWED_HOSTS:
         raise ImproperlyConfigured("ALLOWED_HOSTS não foi definido no ambiente de produção!")

    CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split()
    if not CSRF_TRUSTED_ORIGINS:
        raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS não foi definido no ambiente de produção!")

    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

if WHITENOISE_INSTALLED:
    INSTALLED_APPS.append('whitenoise.runserver_nostatic')

INSTALLED_APPS.append('rachais')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

if WHITENOISE_INSTALLED:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'rachai.urls'
WSGI_APPLICATION = 'rachai.wsgi.application'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


if IS_PRODUCTION:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DBNAME'),
            'HOST': os.environ.get('DBHOST'),
            'USER': os.environ.get('DBUSER'),
            'PASSWORD': os.environ.get('DBPASS'),
            'OPTIONS': {'sslmode': 'require'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'rachais.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'rachais:group_list'
LOGOUT_REDIRECT_URL = 'accounts:login'


LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_TZ = True


STATIC_URL = os.environ.get('DJANGO_STATIC_URL', "/static/")
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'assets',
]
if WHITENOISE_INSTALLED:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
