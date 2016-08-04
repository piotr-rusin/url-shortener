# -*- coding: utf-8 -*-
from flask import session, redirect, url_for, flash, render_template

from . import app
from .forms import ShortenedURLForm
from .models import ShortenedURL, register
from .validation import get_msg_if_blacklisted_or_spam


@app.route('/', methods=['GET', 'POST'])
def shorten_url():
    '''Display form and handle request for url shortening

    If short url is successfully created or found for the
    given url, its alias property is saved in session, and
    the function redirects to its route. After redirection,
    the alias is used to query for newly created shortened
    url, and information about it is presented.

    If there are any errors for data entered by the user into
    the input tex field, they are displayed.

    :returns: a response generated by rendering the template,
    either directly or after redirection.
    '''
    form = ShortenedURLForm()
    KEY = 'requested_alias'
    if form.validate_on_submit():
        shortened_url = ShortenedURL.get_or_create(form.url.data)
        register(shortened_url)
        session[KEY] = str(shortened_url.alias)
        return redirect(url_for(shorten_url.__name__))
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'error')
    try:
        new_shortened_url = ShortenedURL.get_or_404(
            session.pop(KEY)
        )
    except KeyError:
        new_shortened_url = None
    return render_template(
        'shorten_url.html',
        form=form,
        new_shortened_url=new_shortened_url
    )


def render_preview(shortened_url, warning_message=None):
    return render_template(
        'preview.html',
        shortened_url=shortened_url,
        warning=warning_message
    )


def get_response(alias, alternative_action):
    ''' Gets an appropriate response for given alias

    If the alias refers to an url that is recognized as spam or
    containing a blacklisted domain, a preview with information
    on the result of the validation is shown. Otherwise, the function
    returns a result of alternative_action for given alias

    :param alias: a string representing an existing shortened url
    :param alternative_action: a function receiving
    shortened url object as its argument, used for generating
    a response for request for a safe url
    :returns: a response generated from rendering preview or
    calling alternative_action
    :raises werkzeug.exceptions.HTTPException: when there is no
    shortened url for given alias
    '''
    shortened_url = ShortenedURL.get_or_404(alias)
    msg = get_msg_if_blacklisted_or_spam(shortened_url.target)
    if msg is not None:
        return render_preview(shortened_url, msg)
    return alternative_action(shortened_url)


@app.route('/<alias>')
def redirect_for(alias):
    ''' Redirect to address assigned to given alias

    :param alias: a string value by which we search for
    an associated url. If it is not found, a 404 error
    occurs
    :returns: a redirect to target url of short url, if
    found.
    '''
    return get_response(alias, lambda u: redirect(u.target))


@app.route('/preview/<alias>')
def preview(alias):
    ''' Show the preview for given alias

    The preview contains a short url and a target url
    associated with it.

    :param alias: a string value by which we search
    for an associated url. If it is not found, a 404
    error occurs.
    :returns: a response generated from the preview template
    '''
    return get_response(alias, render_preview)


@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html')


@app.errorhandler(500)
def server_error(error):
    return render_template('server_error.html')
