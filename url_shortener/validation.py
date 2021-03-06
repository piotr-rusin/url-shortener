# -*- coding: utf-8 -*-
"""Custom validators."""
from injector import Module, singleton
from spam_lists import (
    GoogleSafeBrowsing, HpHosts, GeneralizedURLTester, URLTesterChain,
    SPAMHAUS_DBL, SPAMHAUS_ZEN, SURBL_MULTI, SortedHostCollection
)
from spam_lists.exceptions import InvalidURLError
from wtforms.validators import ValidationError

from . import __version__, __title__


class BlacklistValidator(object):
    """A URL spam detector using configurable blacklists.

    :ivar _msg_map: a dictionary mapping blacklists used by an instance
    of the class to validation messages associated with them
    """

    def __init__(self, composite_blacklist, default_message):
        """Initialize a new instance.

        :param composite_blacklist: an object representing multiple
        blacklist used by an instance of this class

        It must have lookup_matching(urls) method accepting a sequence
        of URLs and returning an iterator returning other objects, each
        with a source property storing one of the blacklists used by
        the validator - the one containing the item that matches one
        of the URLs.

        It must also have a url_tester property with another property:
        url_testers. The last property represents a chain of blacklist
        objects used by the composite. This property must have
        insert(index, item) method, where :
        * index is a position at which a new blacklist object is
        inserted
        * object is a blacklist object to be inserted
        :param default_message: a default validation message to be
        provided when a URL matches a blacklist that does not have its
        specific validation message
        """
        self._composite_blacklist = composite_blacklist
        self._msg_map = {}
        self.default_message = default_message

    def prepend(self, blacklist, message=None):
        """Add a blacklist to the beginning of the chain.

        :param blacklist: represents a blacklist to be used to
        recognize spam URLs. This object must have
        lookup_matching(urls) method
        :param message: a custom, blacklist-specific validation message
        to be associated with the blacklist, or None if the default
        message is to be associated with the blacklist
        """
        self._composite_blacklist.url_tester.url_testers.insert(0, blacklist)
        if message is not None:
            self._msg_map[blacklist] = message

    def get_msg_if_blacklisted(self, url):
        """Get a message if any response has a blacklisted URL.

        :param url: a URL address as a string
        :returns: a string message if the URL or its redirect addresses
        match content of any of the blacklists, or None
        """
        for match in self._composite_blacklist.lookup_matching([url]):
            return self._msg_map.get(match.source, self.default_message)

    def assert_not_blacklisted(self, form, field):
        """Assert the URL value from the field is not blacklisted.

        This method is a custom WTForms field validator. It supresses
        InvalidURLError, because raising validaion errors is
        the responsibility of wtforms.validators.URL.

        :param form: a form whose field is to be validated
        :param field: a field containing data to be validated
        :raises ValidationError: if the function returns a message
        for the data
        """
        try:
            msg = self.get_msg_if_blacklisted(field.data)
            if msg is not None:
                raise ValidationError(msg)
        except InvalidURLError:
            pass


hp_hosts = HpHosts(__title__)


class ValidationModule(Module):
    """Configures an instance of BlacklistValidator as a dependency.

    The instance is created eagerly.
    """

    def __init__(self, app):
        """Initialize a new instance.

        :param app: an instance of Flask application for which
        the dependency is to be provided.
        """
        self.app = app

    def configure(self, binder):
        """Configure dependencies.

        :param binder: an instance of injector.Binder used for binding
        interfaces to implementations
        """
        binder.bind(
            BlacklistValidator,
            to=self.get_blacklist_url_validator(),
            scope=singleton
        )

    def get_gsb_client(self):
        """Get an instance of Google Safe Browsing Lookup API client."""
        gsb_client = GoogleSafeBrowsing(
            __title__,
            __version__,
            self.app.config['GOOGLE_SAFE_BROWSING_API_KEY']
        )

        self.app.logger.info('Google Safe Browsing API client loaded.')

        return gsb_client

    def get_custom_host_list(self, name, classification, option):
        """Get a custom host blacklist or whitelist.

        :param name: a name of the list to be returned
        :param classification: a classificatory term applied to items
        stored in the list
        :param option: a name of a configuration option storing listed
        items in a free order
        :returns: an instance of SortedHostCollection containing sorted
        items provided in application config file
        """
        host_list = SortedHostCollection(name, classification, [])
        listed = self.app.config[option]
        for item in listed:
            host_list.add(item)

        self.app.logger.info(
            '{} loaded. The number of elements it contains is: {}'.format(
                name.capitalize(),
                len(listed)
            )
        )

        return host_list

    def get_blacklist_url_validator(self):
        """Get a BlacklistValidator object to be provided."""
        return BlacklistValidator(
            GeneralizedURLTester(
                URLTesterChain(
                    self.get_custom_host_list(
                        'custom host blacklist',
                        'blacklisted',
                        'BLACKLISTED_HOSTS'
                    ),
                    self.get_gsb_client(),
                    SURBL_MULTI,
                    SPAMHAUS_ZEN,
                    SPAMHAUS_DBL,
                    hp_hosts
                ),
                whitelist=self.get_custom_host_list(
                    'custom host whitelist',
                    'whitelisted',
                    'WHITELISTED_HOSTS'
                )
            ),
            'The URL has been recognized as spam.'
        )
