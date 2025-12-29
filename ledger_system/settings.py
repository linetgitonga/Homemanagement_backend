import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'jazzmin',  # Jazminn before admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'parler',
    'softdelete',
    'auditlog',
    'fcm_django',
    'core',
    'accounts',
    'finances',
    'analytics',
    'notifications',
    'sync',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
]

ROOT_URLCONF = 'ledger_system.urls'

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

WSGI_APPLICATION = 'ledger_system.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# SECRET_KEY from env (fail if missing)
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("Missing SECRET_KEY environment variable")

# DEBUG from env (defaults to False)
DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')

# ALLOWED_HOSTS from env (comma-separated)
env_allowed = os.getenv('ALLOWED_HOSTS')
if env_allowed:
    ALLOWED_HOSTS = [h.strip() for h in env_allowed.split(',') if h.strip()]
else:
    # Default to common local addresses when running in development (DEBUG=True).
    # When DEBUG=False this will be an empty list and Django will require
    # ALLOWED_HOSTS to be set explicitly (safer for production).
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else []



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'ledger_system'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),  
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True

# Available languages for the project. Parler requires that any language
# codes referenced in `PARLER_LANGUAGES` also exist in `LANGUAGES`.
LANGUAGES = [
    ('en', 'English'),
    ('sw', 'Swahili'),
    ('ki', 'Kikuyu'),
    ('lu', 'Luo'),
]
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Where `collectstatic` will gather static files for production serving
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use WhiteNoise storage so static files are compressed and hashed
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {'anon': '100/day', 'user': '1000/day'},
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

SIMPLE_JWT = {
    # Access/refresh token lifetimes can be configured via environment variables.
    # ACCESS_TOKEN_MINUTES: integer minutes for access token lifetime (default 60)
    # REFRESH_TOKEN_DAYS: integer days for refresh token lifetime (default 7)
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('ACCESS_TOKEN_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('REFRESH_TOKEN_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Ledger System API',
    'DESCRIPTION': 'Household financial management with offline sync',
    'VERSION': '1.2.0',
}

# Auditlog setting: explicitly point to the model used for log entries.
# The default for django-auditlog is 'auditlog.LogEntry'. Defining this
# avoids attribute errors when the package reads settings during app setup.
AUDITLOG_LOGENTRY_MODEL = 'auditlog.LogEntry'

PARLER_LANGUAGES = {
    None: (
        {'code': 'en'},
        {'code': 'sw'},
        {'code': 'ki'},  # Kikuyu
        {'code': 'lu'},  # Luo
    ),
    'default': {'fallback': 'en'}
}

JAZZMIN_SETTINGS = {
    'site_title': "Ledger System Admin",
    'site_header': "Ledger System",
    'site_brand': "L",
    'welcome_sign': "Welcome to Ledger Admin Panel",
    'search_model': ["accounts.User", "finances.Expense", "finances.Category", "accounts.Household"],
    'topmenu_links': [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    'usermenu_links': [
        {"model": "auth.user"},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': ['auditlog', 'auth'],
    'hide_models': [
        'accounts.SystemSettings',
        'sync.SyncLog',
        'auditlog.LogEntry',
    ],
    'order_with_respect_to': ["accounts", "finances", "analytics", "notifications"],
    'custom_links': {},
    'icons': {
        # Accounts App
        "accounts": "fas fa-users",
        "accounts.User": "fas fa-user-circle",
        "accounts.Household": "fas fa-home",
        "accounts.HouseholdMembership": "fas fa-user-friends",
        "accounts.UserNotificationPreferences": "fas fa-bell",
        
        # Finances App
        "finances": "fas fa-wallet",
        "finances.Expense": "fas fa-receipt",
        "finances.Category": "fas fa-tags",
        "finances.Budget": "fas fa-chart-pie",
        "finances.SubExpenseItem": "fas fa-list-ul",
        "finances.ExpenseAttachment": "fas fa-paperclip",
        "finances.RefundRequest": "fas fa-undo-alt",
        
        # Analytics App
        "analytics": "fas fa-chart-line",
        "analytics.Report": "fas fa-file-alt",
        
        # Notifications App
        "notifications": "fas fa-bell",
        "notifications.Notification": "fas fa-envelope",
    },
    'default_icon_parents': "fas fa-folder",
    'default_icon_children': "fas fa-arrow-circle-right",
    'related_modal_active': False,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
    'changeform_format': "horizontal_tabs",
    'changeform_format_overrides': {
        "auth.user": "collapsible", 
        "auth.group": "vertical_tabs",
        "finances.expense": "horizontal_tabs",
        "accounts.household": "horizontal_tabs",
    },
    # UI Tweaks
    'theme': 'flatly',  # Available themes: default, cerulean, cosmo, cyborg, darkly, flatly, journal, litera, lumen, lux, materia, minty, pulse, sandstone, simplex, sketchy, slate, solar, spacelab, superhero, united, yeti
    'dark_mode_theme': 'darkly',  # Set to 'darkly', 'slate', 'solar', or 'superhero' for dark mode
}






# Allow all local network and localhost origins for dev
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.0.0.1:3000",
    "http://10.8.9.195:3000",
    "http://192.168.137.1:3000"
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https?://10\.\d+\.\d+\.\d+:3000$",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]