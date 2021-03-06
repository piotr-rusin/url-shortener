# -*- coding: utf-8 -*-

"""Default configuration for the application.

This configuration file must be supplemented with custom configuration
to which URL_SHORTENER_CONFIGURATION environment variable points,
overriding some of the values specified here.

:var SQLALCHEMY_DATABASE_URI: uri of database to be used by
the application.

The default value serves only as documentation, and it was taken from:
http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls

:var MIN_NEW_ALIAS_LENGTH: a minimum number of characters in a newly
generated alias

:var MAX_NEW_ALIAS_LENGTH: a maximum number of characters in a newly
generated alias

:var SECRET_KEY: a secret key to be used by the application

:var LOG_FILE: a name of file to which the application writes logs.
The value can be None, in which case the application won't write logs
to any file.

If the value is set, it must consist of an existing directory (if any),
but the file doesn't have to exist. The application uses timed roating
file handler with interval of one day, so the file specified here will
be created (if it doesn't exist yet) and used for one day. After that,
it will be renamed, and another file with the same name will be created
in the same directory and used by the application.

:var INTEGRITY_ERROR_LIMIT: a maximum number of integrity errors
allowed to occur when handling a request for a shortened URL before
logging a warning

:var GOOGLE_SAFE_BROWSING_API_KEY: a value necessary for querying
Google Safe Browsing API

:var RECAPTCHA_PUBLIC_KEY: a value used as a public key for reCAPTCHA,
provided by Google: https://developers.google.com/recaptcha/docs/start

:var RECAPTCHA_PRIVATE_KEY: a value used as a private key for reCAPTCHA,
provided by Google: https://developers.google.com/recaptcha/docs/start

:var ADMIN_EMAIL: email address of administrator(s) of the service provided
by an installation of this application

:var BLACKLISTED_HOSTS: a custom list of strings representing blacklisted
hosts

:var WHITELISTED_HOSTS: a custom list of strings representing whitelisted
hosts. URLs with them will not be tested against blacklist.
"""
SQLALCHEMY_DATABASE_URI = (
    'dialect+driver://username:password@host:port/database'
)
MIN_NEW_ALIAS_LENGTH = 3
MAX_NEW_ALIAS_LENGTH = 5
SECRET_KEY = 'a secret key'
LOG_FILE = None
INTEGRITY_ERROR_LIMIT = 10
GOOGLE_SAFE_BROWSING_API_KEY = 'a key'
RECAPTCHA_PUBLIC_KEY = 'public-recaptcha-key'
RECAPTCHA_PRIVATE_KEY = 'private-recaptcha-key'
ADMIN_EMAIL = 'admin@your-domain.com'
BLACKLISTED_HOSTS = []
WHITELISTED_HOSTS = []
