# -*- coding: utf-8 -*-
import datetime

from flask import redirect, url_for, flash, render_template, Markup
from flask.views import View
from injector import inject

from . import app
from .forms import url_form_class
from .models import AliasValueError, commit_changes, target_url_class

from .validation import BlacklistValidator


@app.context_processor
def inject_year():
    now = datetime.datetime.now()
    return dict(year=now.year)


@inject
@app.route('/', methods=['GET', 'POST'])
def shorten_url(
    target_url_class: target_url_class,
    form_class: url_form_class,
    commit_changes: commit_changes
):
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
    form = form_class()
    if form.validate_on_submit():
        target_url = target_url_class.get_or_create(form.url.data)
        commit_changes()
        url_tpl = Markup('{0}: <a href="{1}"{2}>{1}</a>')
        description_url_map = (
            ('Original URL', target_url, ' class=truncated'),
            ('Short URL', target_url.short_url, ''),
            ('Preview available at', target_url.preview_url, '')
        )
        for data in description_url_map:
            flash(url_tpl.format(*data))

        return redirect(url_for(shorten_url.__name__))

    return render_template('shorten_url.html', form=form)


class ShowURL(View):
    """A class of views presenting existing target URLs

    The target URLs can be presented either by redirecting to them or
    by showing a preview page containing the target URL and a short URL
    redirecting to it and provided by the application.
    """

    @inject
    def __init__(
        self,
        preview,
        target_url_class: target_url_class,
        blacklist_validator: BlacklistValidator
    ):
        """ Initialize a new instance

        :param preview: if True, the response returned by the view will
        always be a preview of target URL with given alias. If False,
        it will be a redirect to the target URL, unless blacklist
        validator recognizes URL as spam, in which case it will be
        the preview.
        :param target_url_class: an instance of target_url_class used
        to look up the URL
        :param blacklist_validator: an instance of BlacklistValidator
        used to test if the URL is recognized as spam
        """

        self.preview = preview
        self.target_url_class = target_url_class
        self.blacklist_validator = blacklist_validator

    def dispatch_request(self, alias):
        """Show URL either as a redirection to target or as a preview
        of target URL

        :param alias: a string value by which we search for
        an associated URL. If it is not found, a 404 error occurs.
        :returns: a response depending on results of blacklist lookup
        and initial configuration of the view
        :raises werkzeug.exception.HTTPException with code 404, if
        it is raised by the target URL search call
        """
        target_url = self.target_url_class.query.get_or_404(alias)
        spam_msg = self.blacklist_validator.get_msg_if_blacklisted(
            str(target_url)
        )

        if spam_msg or self.preview:
            return render_template(
                'preview.html',
                target_url=target_url,
                warning=spam_msg
            )
        return redirect(target_url)


app.add_url_rule(
    '/<alias>',
    view_func=ShowURL.as_view('redirect_for', preview=False)
)

app.add_url_rule(
    '/preview/<alias>',
    view_func=ShowURL.as_view('preview', preview=True)
)


@app.errorhandler(AliasValueError)
@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html')


@app.errorhandler(500)
def server_error(error):
    return render_template('server_error.html')
