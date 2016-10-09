# -*- coding: utf-8 -*-
import datetime

from flask import (
    redirect, url_for, flash, render_template, Markup
)

from . import app
from .forms import ShortenedURLForm
from .models import (
    TargetURL, shorten_if_new, URLNotShortenedError, AliasValueError
)
from .validation import url_validator


@app.context_processor
def inject_year():
    now = datetime.datetime.now()
    return dict(year=now.year)


@app.route('/', methods=['GET', 'POST'])
def shorten_url():
    """Display form and handle request for URL shortening

    If short URL is successfully created or found for the
    given URL, its alias property is saved in session, and
    the function redirects to its route. After redirection,
    the alias is used to query for newly created shortened
    URL, and information about it is presented.

    If there are any errors for data entered by the user into
    the input text field, they are displayed.

    :returns: a response generated by rendering the template,
    either directly or after redirection.
    """
    form = ShortenedURLForm()
    if form.validate_on_submit():
        target_url = TargetURL.get_or_create(form.url.data)
        try:
            shorten_if_new(target_url, app.config['ATTEMPT_LIMIT'])
            msg_tpl = Markup(
                'New short URL: <a href="{0}">{0}</a><br>Preview'
                ' available at: <a href="{1}">{1}</a>'
            )
            msg = msg_tpl.format(target_url.short_url, target_url.preview_url)
            flash(msg, 'success')

            return redirect(url_for(shorten_url.__name__))
        except URLNotShortenedError as ex:
            app.logger.error(ex)
            msg_tpl = Markup(
                'Failed to generate a unique short alias for requested URL.'
                ' Please, try again.<br> If you see this error again,'
                ' <a href="{}">send us a message</a>'
            )
            msg = msg_tpl.format(app.config['ADMIN_EMAIL'])
            flash(msg, 'error')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'error')
    return render_template('shorten_url.html', form=form)


def render_preview(target_url, warning_message=None):
    return render_template(
        'preview.html',
        target_url=target_url,
        warning=warning_message
    )


def get_response(alias, alternative_action):
    """ Gets an appropriate response for given alias

    If the alias refers to a URL that is recognized as spam or
    containing a blacklisted domain, a preview with information
    on the result of the validation is shown. Otherwise, the function
    returns a result of alternative_action for given alias

    :param alias: a string representing an existing target URL
    :param alternative_action: a function receiving
    target URL object as its argument, used for generating
    a response for request for a safe URL
    :returns: a response generated from rendering preview or
    calling alternative_action
    :raises werkzeug.exceptions.HTTPException: when there is no
    target URL for given alias
    """
    target_url = TargetURL.get_or_404(alias)
    msg = url_validator.get_msg_if_blacklisted(target_url.value)
    if msg is not None:
        return render_preview(target_url, msg)
    return alternative_action(target_url)


@app.route('/<alias>')
def redirect_for(alias):
    """ Redirect to address assigned to given alias

    :param alias: a string value by which we search for
    an associated URL. If it is not found, a 404 error
    occurs
    :returns: a redirect to target URL of short URL, if
    found.
    """
    return get_response(alias, redirect)


@app.route('/preview/<alias>')
def preview(alias):
    """ Show the preview for given alias

    The preview contains a short URL and a target URL
    associated with it.

    :param alias: a string value by which we search
    for an associated URL. If it is not found, a 404
    error occurs.
    :returns: a response generated from the preview template
    """
    return get_response(alias, render_preview)


@app.errorhandler(AliasValueError)
@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html')


@app.errorhandler(500)
def server_error(error):
    return render_template('server_error.html')
