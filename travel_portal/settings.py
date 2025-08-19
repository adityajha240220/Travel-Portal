from pathlib import Path
import os
from dotenv import load_dotenv
import secrets

# Load .env file for LOCAL development
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CORE DJANGO SETTINGS ---

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", secrets.token_urlsafe(50))  # Strong fallback for dev
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
# Set DJANGO_DEBUG=False on Render for production

ALLOWED_HOSTS = []
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")
if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost', 'travel-portal-2.onrender.com'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'planner',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'travel_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'accounts' / 'templates' / 'accounts'],
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

WSGI_APPLICATION = 'travel_portal.wsgi.application'

# --- DATABASE CONFIGURATION ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# For Render production, use DATABASE_URL from env vars for PostgreSQL

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.CustomUser'

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES CONFIGURATION ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- DEFAULT PRIMARY KEY FIELD TYPE ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- DJANGO REST FRAMEWORK CONFIGURATION ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# --- CORS HEADERS CONFIGURATION ---
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:3000",
    "https://travel-portal-2.onrender.com",
]
CORS_ALLOW_CREDENTIALS = True  # If needed for auth tokens
# Removed insecure option and added CSRF trusted origins for better security
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://travel-portal-2.onrender.com",
]