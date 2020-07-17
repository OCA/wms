from .common import CommonCase


class ZonePickingCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_zone_picking")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.menu.picking_type_ids

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # We want to limit the tests to a dedicated location in Stock/ to not
        # be bothered with pickings brought by demo data
        cls.zone_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone location",
                    "location_id": cls.stock_location.id,
                    "barcode": "ZONE_LOCATION",
                }
            )
        )
        cls.zone_sublocation = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION",
                }
            )
        )
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.zone_sublocation
        )
        cls._fill_stock_for_moves(picking2.move_lines, location=cls.zone_sublocation)
        cls.pickings.action_assign()

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="zone_picking")

    def assert_response_start(self, response, message=None):
        self.assert_response(response, next_state="start", message=message)

    def _assert_response_select_picking_type(
        self, state, response, zone_location, picking_types, message=None
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_types": self.data.picking_types(picking_types),
            },
            message=message,
        )

    def assert_response_select_picking_type(
        self, response, zone_location, picking_types, message=None
    ):
        self._assert_response_select_picking_type(
            "select_picking_type",
            response,
            zone_location,
            picking_types,
            message=message,
        )
