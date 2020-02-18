from contextlib import contextmanager
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

    def __eq__(self, other):
        return True


class CommonCase(SavepointCase, ComponentMixin):

    # by default disable tracking suite-wise, it's a time saver :)
    tracking_disable = True

    ANY = AnyObject()

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
        cls.setUpClassVars()

    @classmethod
    def setUpClassVars(cls):
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location = stock_location
        cls.dispatch_location = cls.env.ref("stock.location_dispatch_zone")
        cls.dispatch_location.barcode = "DISPATCH"
        cls.packing_location = cls.env.ref("stock.location_pack_zone")
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.shelf2 = cls.env.ref("stock.stock_location_14")
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def assert_response(self, response, next_state=None, message=None, data=None):
        """Assert a response from the webservice

        The data and message dictionaries can use ``self.ANY`` to accept any
        value.
        """
        expected = {}
        if message:
            expected["message"] = message
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

    def _update_qty_in_location(self, location, product, quantity):
        self.env["stock.quant"]._update_available_quantity(product, location, quantity)

    def _fill_stock_for_pickings(self, pickings):
        product_locations = {}
        for move in pickings.mapped("move_lines"):
            key = (move.product_id, move.location_id)
            product_locations.setdefault(key, 0)
            product_locations[key] += move.product_qty
        for (product, location), qty in product_locations.items():
            self._update_qty_in_location(location, product, qty)
