"""
Django settings for aulatrack project.
Optimizado para Render + funcionamiento local.
"""

from pathlib import Path
import os

# ============================
# BASE
# ============================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-i0zs+wbc0rtgz)&-5a!ft(=slfrh29@5n5vxg3+#m@ra9dquf1'

# ============================
# DEBUG AUTOMÁTICO
# Local = True
# Render = False
# ============================
DEBUG = os.environ.get("RENDER") != "true"

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'prueba-render-0fd9.onrender.com',
]

# ============================
# APPS
# ============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
]

AUTH_USER_MODEL = 'usuarios.Usuario'

# ============================
# STATIC FILES (CSS / JS / IMG)
# ============================
STATIC_URL = '/static/'

# Donde Render guardará los archivos procesados
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Donde están tus archivos reales
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise para servir archivos ya comprimidos
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ============================
# MIDDLEWARE
# ============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 🔥 NECESARIO PARA RENDER
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================
# TEMPLATES
# ============================
ROOT_URLCONF = 'aulatrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aulatrack.wsgi.application'

# ============================
# BASE DE DATOS
# ============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================
# VALIDADORES CONTRASEÑAS
# ============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================
# INTERNACIONALIZACIÓN
# ============================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================
# LOGIN Y REDIRECCIONES
# ============================
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'usuarios:home_page'
LOGOUT_REDIRECT_URL = 'usuarios:login'
