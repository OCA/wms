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
        cls.zone_sublocation1 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location 1",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION_1",
                }
            )
        )
        cls.zone_sublocation2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location 2",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION_2",
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

        cls.picking1 = picking1 = cls._create_picking(lines=[(cls.product_a, 10)])
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_b, 10), (cls.product_c, 10)]
        )
        cls.pickings = picking1 | picking2
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.zone_sublocation1
        )
        cls._fill_stock_for_moves(
            picking2.move_lines, in_lot=True, location=cls.zone_sublocation2
        )
        cls.pickings.action_assign()
        # Some records not related at all to the processed move lines
        cls.free_package = cls.env["stock.quant.package"].create(
            {"name": "FREE_PACKAGE"}
        )
        cls.free_lot = cls.env["stock.production.lot"].create(
            {
                "name": "FREE_LOT",
                "product_id": cls.product_a.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.free_product = (
            cls.env["product.product"]
            .sudo()
            .create({"name": "FREE_PRODUCT", "barcode": "FREE_PRODUCT"})
        )

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

    def _assert_response_select_line(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_lines,
        message=None,
        popup=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_lines": self.data.move_lines(move_lines),
            },
            message=message,
            popup=popup,
        )

    def assert_response_select_line(
        self,
        response,
        zone_location,
        picking_type,
        move_lines,
        message=None,
        popup=None,
    ):
        self._assert_response_select_line(
            "select_line",
            response,
            zone_location,
            picking_type,
            move_lines,
            message=message,
            popup=popup,
        )

    def _assert_response_set_line_destination(
        self, state, response, zone_location, picking_type, move_line, message=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_line": self.data.move_line(move_line),
            },
            message=message,
        )

    def assert_response_set_line_destination(
        self, response, zone_location, picking_type, move_line, message=None,
    ):
        self._assert_response_set_line_destination(
            "set_line_destination",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
        )
