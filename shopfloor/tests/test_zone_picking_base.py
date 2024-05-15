# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase

# pylint: disable=missing-return


class ZonePickingCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_zone_picking")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        Users = cls.env["res.users"].sudo().with_context(no_reset_password=True)
        cls.stock_user2 = Users.create(
            {
                "name": "Paul Posichon",
                "login": "paulposichon",
                "email": "paul.posichon@example.com",
                "notification_type": "inbox",
                "groups_id": [(6, 0, [cls.env.ref("stock.group_stock_user").id])],
            }
        )

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.packing_location.sudo().active = True
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
        # Set default location for our picking type
        cls.menu.picking_type_ids[0].sudo().default_location_src_id = cls.zone_location
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
        cls.zone_sublocation3 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location 3",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION_3",
                }
            )
        )
        cls.zone_sublocation4 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location 4",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION_4",
                }
            )
        )
        cls.zone_sublocation5 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Zone sub-location 5",
                    "location_id": cls.zone_location.id,
                    "barcode": "ZONE_SUBLOCATION_5",
                }
            )
        )
        cls.packing_sublocation_a = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing Sublocation A",
                    "location_id": cls.packing_location.id,
                    "barcode": "PACKING_SUBLOCATION_A",
                }
            )
        )
        cls.packing_sublocation_b = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Packing Sublocation B",
                    "location_id": cls.packing_location.id,
                    "barcode": "PACKING_SUBLOCATION_B",
                }
            )
        )
        cls.product_e = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product E",
                    "type": "product",
                    "default_code": "E",
                    "barcode": "E",
                    "weight": 3,
                }
            )
        )
        cls.product_f = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product F",
                    "type": "product",
                    "default_code": "F",
                    "barcode": "F",
                    "weight": 3,
                }
            )
        )
        cls.product_g = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product G",
                    "type": "product",
                    "default_code": "G",
                    "barcode": "G",
                    "weight": 3,
                }
            )
        )
        cls.product_h = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product H",
                    "type": "product",
                    "default_code": "H",
                    "barcode": "H",
                    "weight": 3,
                }
            )
        )
        cls.product_i = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product I",
                    "type": "product",
                    "default_code": "I",
                    "barcode": "I",
                    "weight": 3,
                }
            )
        )
        products = (
            cls.product_a
            + cls.product_b
            + cls.product_c
            + cls.product_d
            + cls.product_e
            + cls.product_f
            + cls.product_g
            + cls.product_h
            + cls.product_i
        )
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        # 1 product in a package available in zone_sublocation1
        cls.picking1 = picking1 = cls._create_picking(lines=[(cls.product_a, 10)])
        cls._fill_stock_for_moves(
            picking1.move_ids, in_package=True, location=cls.zone_sublocation1
        )
        # 2 products with lots available in zone_sublocation2
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_b, 10), (cls.product_c, 10)]
        )
        cls._fill_stock_for_moves(
            picking2.move_ids, in_lot=True, location=cls.zone_sublocation2
        )
        # 1 product (no package, no lot) available in zone_sublocation3
        cls.picking3 = picking3 = cls._create_picking(lines=[(cls.product_d, 10)])
        cls._fill_stock_for_moves(picking3.move_ids, location=cls.zone_sublocation3)
        # 1 product, available in zone_sublocation3 and zone_sublocation4
        # Put product_e quantities in two different source locations to get
        # two stock move lines (6 and 4 to satisfy 10 qties)
        cls.picking4 = picking4 = cls._create_picking(lines=[(cls.product_e, 10)])
        cls._update_qty_in_location(cls.zone_sublocation3, cls.product_e, 6)
        cls._update_qty_in_location(cls.zone_sublocation4, cls.product_e, 4)
        # 2 products in a package available in zone_sublocation4
        cls.picking5 = picking5 = cls._create_picking(
            lines=[(cls.product_i, 10), (cls.product_f, 10)]
        )
        cls._fill_stock_for_moves(
            picking5.move_ids,
            in_package=True,
            same_package=True,
            location=cls.zone_sublocation4,
        )
        # 2 products available in zone_sublocation5, but one is partially available
        cls.picking6 = picking6 = cls._create_picking(
            lines=[(cls.product_g, 6), (cls.product_h, 6)]
        )
        cls._update_qty_in_location(cls.zone_sublocation5, cls.product_g, 6)
        cls._update_qty_in_location(cls.zone_sublocation5, cls.product_h, 3)

        cls.pickings = picking1 | picking2 | picking3 | picking4 | picking5 | picking6
        cls.pickings.action_assign()
        # Some records not related at all to the processed move lines
        cls.free_package = cls.env["stock.quant.package"].create(
            {"name": "FREE_PACKAGE"}
        )
        cls.free_lot = cls.env["stock.lot"].create(
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
        self.service = self.get_service(
            "zone_picking",
            menu=self.menu,
            profile=self.profile,
            current_zone_location=self.zone_location,
            current_picking_type=self.picking_type,
        )
        self.menu.sudo().allow_alternative_destination_package = True

    def _assert_response_select_zone(self, response, zone_locations, message=None):
        data = {"zones": self.service._data_for_select_zone(zone_locations)}
        self.assert_response(
            response,
            next_state="start",
            data=data,
            message=message,
        )

    def assert_response_start(self, response, zone_locations=None, message=None):
        if zone_locations is None:
            zone_locations = self.zone_location.child_ids
        self._assert_response_select_zone(response, zone_locations, message=message)

    def _assert_response_select_picking_type(
        self, state, response, zone_location, picking_types, message=None
    ):
        data = self.service._data_for_select_picking_type(zone_location, picking_types)
        self.assert_response(
            response,
            next_state=state,
            data=data,
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
        confirmation_required=None,
        product=None,
        sublocation=None,
        location_first=None,
        package=None,
    ):
        data = {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "move_lines": self.data.move_lines(move_lines, with_picking=True),
            "confirmation_required": confirmation_required,
            "scan_location_or_pack_first": location_first,
        }
        if product:
            data["product"] = self.data.product(product)
        if package:
            data["package"] = self.data.package(package)
        if sublocation:
            data["sublocation"] = self.data.location(sublocation)
        for data_move_line in data["move_lines"]:
            move_line = self.env["stock.move.line"].browse(data_move_line["id"])
            data_move_line[
                "location_will_be_empty"
            ] = move_line.location_id.planned_qty_in_location_is_empty(move_line)
            data_move_line[
                "handle_complete_mix_pack"
            ] = self.service._handle_complete_mix_pack(move_line.package_id)
        self.assert_response(
            response,
            next_state=state,
            data=data,
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
        confirmation_required=None,
        product=None,
        sublocation=None,
        location_first=False,
        package=False,
    ):
        self._assert_response_select_line(
            "select_line",
            response,
            zone_location,
            picking_type,
            move_lines,
            message=message,
            popup=popup,
            confirmation_required=confirmation_required,
            product=product,
            sublocation=sublocation,
            location_first=location_first,
            package=package,
        )

    def _assert_response_set_line_destination(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=None,
        qty_done=None,
        handle_complete_mix_pack=False,
    ):
        expected_move_line = self.data.move_line(move_line, with_picking=True)
        if qty_done is not None:
            expected_move_line["qty_done"] = qty_done
        allow_alternative_destination_package = (
            self.menu.allow_alternative_destination_package
        )
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_line": expected_move_line,
                "confirmation_required": confirmation_required,
                "allow_alternative_destination_package": allow_alternative_destination_package,
                "handle_complete_mix_pack": handle_complete_mix_pack,
            },
            message=message,
        )

    def assert_response_set_line_destination(
        self,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=None,
        qty_done=None,
        handle_complete_mix_pack=False,
    ):
        self._assert_response_set_line_destination(
            "set_line_destination",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
            confirmation_required=confirmation_required,
            qty_done=qty_done,
            handle_complete_mix_pack=handle_complete_mix_pack,
        )

    def _assert_response_zero_check(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "location": self.data.location(move_line.location_id),
                "move_line": self.data.move_line(move_line),
            },
            message=message,
        )

    def assert_response_zero_check(
        self,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
    ):
        self._assert_response_zero_check(
            "zero_check",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
        )

    def _assert_response_change_pack_lot(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_line": self.data.move_line(move_line, with_picking=True),
            },
            message=message,
        )

    def assert_response_change_pack_lot(
        self,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
    ):
        self._assert_response_change_pack_lot(
            "change_pack_lot",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
        )

    def _assert_response_unload_set_destination(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_line": self.data.move_line(move_line, with_picking=True),
                "confirmation_required": confirmation_required,
            },
            message=message,
        )

    def assert_response_unload_set_destination(
        self,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=None,
    ):
        self._assert_response_unload_set_destination(
            "unload_set_destination",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
            confirmation_required=confirmation_required,
        )

    def _assert_response_unload_all(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_lines,
        message=None,
        confirmation_required=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_lines": self.data.move_lines(move_lines, with_picking=True),
                "confirmation_required": confirmation_required,
            },
            message=message,
        )

    def assert_response_unload_all(
        self,
        response,
        zone_location,
        picking_type,
        move_lines,
        message=None,
        confirmation_required=None,
    ):
        self._assert_response_unload_all(
            "unload_all",
            response,
            zone_location,
            picking_type,
            move_lines,
            message=message,
            confirmation_required=confirmation_required,
        )

    def _assert_response_unload_single(
        self,
        state,
        response,
        zone_location,
        picking_type,
        move_line,
        message=None,
        popup=None,
    ):
        self.assert_response(
            response,
            next_state=state,
            data={
                "zone_location": self.data.location(zone_location),
                "picking_type": self.data.picking_type(picking_type),
                "move_line": self.data.move_line(move_line, with_picking=True),
            },
            message=message,
            popup=popup,
        )

    def assert_response_unload_single(
        self, response, zone_location, picking_type, move_line, message=None, popup=None
    ):
        self._assert_response_unload_single(
            "unload_single",
            response,
            zone_location,
            picking_type,
            move_line,
            message=message,
            popup=popup,
        )
