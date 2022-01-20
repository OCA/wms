# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from contextlib import contextmanager
from pprint import pformat

import mock

from odoo.tests.common import SavepointCase

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.base_rest.tests.common import RegistryMixin
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import ComponentMixin


class AnyObject:
    def __repr__(self):
        return "ANY"

    def __deepcopy__(self, memodict=None):
        return self

    def __copy__(self):
        return self

    def __eq__(self, other):
        return True


class CommonCase(SavepointCase, RegistryMixin, ComponentMixin):
    """Base class for writing Shopfloor tests

    All tests are run as normal stock user by default, to check that all the
    services work without manager permissions.

    The consequences on writing tests:

    * Records created or written in a test setup must use sudo()
      if the user has no permission on these models.
    * Tests setUps should not extend setUpClass but setUpClassVars
      and setUpClassBaseData, which already have an environment using
      the stock user.
    * Be wary of creating records before setUpClassUsers is called, because
      it their "env.user" would be admin and could lead to inconsistencies
      in tests.

    This class provides several helpers which are used throughout all the tests.
    """

    # by default disable tracking suite-wise, it's a time saver :)
    tracking_disable = True

    ANY = AnyObject()  # allow accepting anything in assert_response()

    maxDiff = None

    @contextmanager
    def work_on_services(self, collection=None, env=None, **params):
        collection = collection or self.shopfloor_app
        if env:
            collection = collection.with_env(env)
        params = params or {}
        yield WorkContext(
            model_name="rest.service.registration",
            collection=collection,
            # No need for a real request mock
            # as we don't deal w/ real request for testing
            # but base_rest context provider needs it.
            request=mock.Mock(),
            **params
        )

    def get_service(self, usage, collection=None, env=None, **kw):
        with self.work_on_services(collection=collection, env=env, **kw) as work:
            service = work.component(usage=usage)
            # Thanks to shopfloor.app we don't need controllers
            # but not having a controller means that non decorated methods
            # stay undecorated as they are not fixed at startup by base_rest.
            self.env["shopfloor.app"]._prepare_non_decorated_endpoints(service)
            return service

    @contextmanager
    def work_on_actions(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.action", self.env)
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
            context=dict(
                cls.env.context,
                tracking_disable=cls.tracking_disable,
                _service_skip_request_validation=True,
            )
        )
        cls.setUpComponent()
        cls.setUpRegistry()
        cls.setUpClassUsers()
        cls.setUpClassVars()
        cls.setUpClassBaseData()

        # Keep this here to have the whole env set up already
        cls.setUpShopfloorApp()

        with cls.work_on_actions(cls) as work:
            cls.data = work.component(usage="data")
            cls.data_detail = work.component(usage="data_detail")
            cls.msg_store = work.component(usage="message")
            cls.schema = work.component(usage="schema")
            cls.schema_detail = work.component(usage="schema_detail")

    @classmethod
    def setUpClassUsers(cls):
        Users = cls.env["res.users"].with_context(
            {"no_reset_password": True, "mail_create_nosubscribe": True}
        )
        cls.shopfloor_user = Users.create(cls._shopfloor_user_values())
        cls.shopfloor_manager = Users.create(cls._shopfloor_manager_values())
        cls.env = cls.env(user=cls.shopfloor_user)

    @classmethod
    def _shopfloor_user_values(cls):
        return {
            "name": "Pauline Poivraisselle",
            "login": "pauline2",
            "email": "p.p@example.com",
            "groups_id": [
                (6, 0, [cls.env.ref("shopfloor_base.group_shopfloor_user").id])
            ],
            "tz": cls.env.user.tz,
        }

    @classmethod
    def _shopfloor_manager_values(cls):
        return {
            "name": "Johnny Manager",
            "login": "jmanager",
            "email": "jmanager@example.com",
            "groups_id": [
                (6, 0, [cls.env.ref("shopfloor_base.group_shopfloor_manager").id])
            ],
            "tz": cls.env.user.tz,
        }

    @classmethod
    def setUpClassVars(cls):
        pass

    @classmethod
    def setUpClassBaseData(cls):
        pass

    @classmethod
    def setUpShopfloorApp(cls):
        cls.shopfloor_app = (
            cls.env["shopfloor.app"]
            .with_user(cls.shopfloor_manager)
            .create(
                {
                    "tech_name": "test",
                    "name": "Test",
                    "short_name": "test",
                }
            )
            .with_user(cls.shopfloor_user)
        )

    def assert_response(
        self, response, next_state=None, message=None, data=None, popup=None
    ):
        """Assert a response from the webservice

        The data and message dictionaries can use ``self.ANY`` to accept any
        value.
        """
        expected = {}
        if message:
            expected["message"] = message
        if popup:
            expected["popup"] = popup
        if next_state:
            expected.update(
                {"next_state": next_state, "data": {next_state: data or {}}}
            )
        elif data:
            expected["data"] = data
        self.assertDictEqual(
            response,
            expected,
            "\n\nActual:\n%s"
            "\n\nExpected:\n%s" % (pformat(response), pformat(expected)),
        )
