from contextlib import contextmanager
from copy import deepcopy
from pprint import pformat

from odoo.tests.common import SavepointCase

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import ComponentMixin


class AnyObject:
    def __repr__(self):
        return "ANY"

    def __deepcopy__(self, memodict=None):
        return self

    def __copy__(self):
        return self


class CommonCase(SavepointCase, ComponentMixin):

    # by default disable tracking suite-wise, it's a time saver :)
    tracking_disable = True

    @contextmanager
    def work_on_services(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.service", self.env)
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )

    # pylint: disable=method-required-super
    # super is called "the old-style way" to call both super classes in the
    # order we want
    def setUp(self):
        # Have to initialize both odoo env and stuff +
        # the Component registry of the mixin
        SavepointCase.setUp(self)
        ComponentMixin.setUp(self)

    @classmethod
    def setUpClass(cls):
        super(CommonCase, cls).setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=cls.tracking_disable)
        )
        cls.setUpComponent()

    def assert_response(self, response, state=None, message=None, data=None):
        """Assert a response from the webservice

        The data and message dictionaries are checked using
        ``self.assert_dict``, which means we can use ``self.ANY`` to accept any
        value.
        """
        expected = {}
        if state:
            expected["state"] = state
        if message:
            expected["message"] = message
        if data:
            expected["data"] = data
        self.assert_dict(response, expected)

    ANY = AnyObject()

    def assert_dict(self, current, expected):
        """Assert dictionary equality with support of wildcard values

        In the expected dictionary, instead of a value, ``self.ANY``
        can be provided, which will accept any value.

        For instance, an expected value for a response which accepts any
        content could be::

            {
                "data": self.ANY,
                "message": {
                    "title": self.ANY,
                    "message_type": self.ANY,
                    "message": self.ANY,
                },
                "state": self.ANY,
            }

        Note: if ``self.ANY`` is used, the key must exist in the dictionary
        to check.
        """
        next_checks = [(current, expected)]
        while next_checks:
            original, node_original_expected = next_checks.pop()
            node_values = deepcopy(original)
            node_expected = deepcopy(node_original_expected)

            for key in original:
                # sub-dictionaries will be checked later
                expected_value = node_expected.get(key)
                if expected_value is self.ANY:
                    # ignore 'any' keys
                    node_values.pop(key)
                    node_expected.pop(key)
                    continue
                if isinstance(expected_value, dict):
                    next_checks.append((node_values.pop(key), node_expected.pop(key)))
                    continue

            self.assertDictEqual(
                node_values,
                node_expected,
                "\n\nNode's specs:\n%s" % (pformat(node_original_expected)),
            )
