# -*- coding: utf-8 -*-

"""Builtin server execution module."""
from url_shortener import get_app_and_db

app, _ = get_app_and_db('URL_SHORTENER_CONFIGURATION', from_envvar=True)

app.run()
