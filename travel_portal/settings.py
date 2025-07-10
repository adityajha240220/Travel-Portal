# Travel_Portal/Travel_Portal/settings.py

from pathlib import Path
import os
from dotenv import load_dotenv

# ✅ Load .env file for LOCAL development
# On Render, environment variables are loaded by the platform,
# so this line is primarily for local use.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CORE DJANGO SETTINGS ---

# SECURITY WARNING: keep the secret key used in production secret!
# Use an environment variable for the secret key.
# The fallback is for local development ONLY.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 'your-super-secret-fallback-key-for-dev')
# IMPORTANT: For Render, set DJANGO_SECRET_KEY in your Render environment variables
# with a STRONG, unique value (e.g., secrets.token_urlsafe(50)).

# SECURITY WARNING: don't run with debug turned on in production!
# Debug mode should be controlled by an environment variable.
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
# IMPORTANT: For Render production, set DEBUG to 'False' in your Render environment variables.

# Allowed hosts for the Django application.
# This is crucial for security.
#
# In production on Render, set the ALLOWED_HOSTS environment variable to
# 'travel-portal-1.onrender.com' (and any other custom domains, separated by commas).
# Example environment variable value on Render:
# ALLOWED_HOSTS = travel-portal-1.onrender.com,your.custom.domain.com
#
ALLOWED_HOSTS = []
# If ALLOWED_HOSTS environment variable is set, use it.
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

# If in DEBUG mode and not already present, add common local development hosts.
# This helps in local testing without needing to set ALLOWED_HOSTS env var locally.
if DEBUG:
    if '127.0.0.1' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('127.0.0.1')
    if 'localhost' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('localhost')

# !!! TEMPORARY DEBUGGING: Print the final ALLOWED_HOSTS list to Render logs !!!
# Deploy with this line, check your Render logs, then REMOVE THIS LINE.
print(f"--- DEBUG: ALLOWED_HOSTS effective list: {ALLOWED_HOSTS} ---")

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
    'whitenoise.runserver_nostatic', # Add this for WhiteNoise in development
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise middleware should be placed directly after SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Keep this here or after CommonMiddleware
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

# --- DATABASE CONFIGURATION (SQLite3 for persistence concerns) ---
# IMPORTANT: SQLite3 is NOT recommended for production on Render's ephemeral filesystem.
# Data stored in db.sqlite3 will be LOST on every redeploy or server restart.
# Consider switching to a persistent database like PostgreSQL on Render for production data.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES CONFIGURATION (CRUCIAL FOR PRODUCTION) ---
STATIC_URL = 'static/'
# This is the directory where `collectstatic` will gather all static files.
# It should be outside your project directory in production for WhiteNoise.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Set a specific STATIC_ROOT

# Configure WhiteNoise to serve static files efficiently in production.
# Install WhiteNoise: pip install whitenoise
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
    ]
}

# --- CORS HEADERS CONFIGURATION ---
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    # Add any other origins where your frontend might be running (e.g., "http://localhost:3000")
    # Add your Render domain here, as it's the host from which your frontend (if separate) or API will be accessed.
    "https://travel-portal-1.onrender.com",
    # If you have a separate frontend on Render or another host, add its URL here:
    # "https://your-separate-frontend-app.onrender.com",
    # "https://your-custom-frontend-domain.com",
]

# You might also need to configure CORS_ALLOW_ALL_ORIGINS = True for quick testing,
# but it's generally insecure for production. If you use it, replace it with
# specific origins as soon as possible.
# CORS_ALLOW_ALL_ORIGINS = True # USE WITH EXTREME CAUTION IN PRODUCTION!