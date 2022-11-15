# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.common import CommonCase


class ManualProductTransferCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref(
            "shopfloor_manual_product_transfer.shopfloor_menu_manual_product_transfer"
        )
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.not_allowed_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Not Allowed Source Location",
                    "barcode": "NOT_ALLOWED_SRC_LOC",
                }
            )
        )
        cls.empty_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Empty Source Location",
                    "barcode": "EMPTY_SRC_LOC",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        cls.src_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Source Location",
                    "barcode": "SRC_LOC",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        cls.product_b.tracking = "lot"
        cls.product_b_lot = cls.env["stock.production.lot"].create(
            {
                "name": "LOT",
                "product_id": cls.product_b.id,
                "company_id": cls.wh.company_id.id,
            }
        )
        cls._update_qty_in_location(
            cls.src_location,
            cls.product_a,
            10,
        )
        cls._update_qty_in_location(
            cls.src_location, cls.product_b, 10, lot=cls.product_b_lot
        )

    @classmethod
    def setUpShopfloorApp(cls):
        super().setUpShopfloorApp()
        cls.shopfloor_app.sudo().profile_ids += cls.profile

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "manual_product_transfer", profile=self.profile, menu=self.menu
        )

    def assert_response_start(self, response, message=None):
        self.assert_response(response, next_state="start", message=message)

    def assert_response_scan_product(self, response, location, message=None):
        self.assert_response(
            response,
            next_state="scan_product",
            data={"location": self.data.location(location)},
            message=message,
        )

    def assert_response_confirm_quantity(
        self,
        response,
        location,
        product,
        quantity,
        lot=None,
        warning=None,
        message=None,
    ):
        data = {
            "location": self.data.location(location),
            "product": self.data.product(product),
            "quantity": quantity,
            "warning": warning,
        }
        if lot:
            data.update(lot=self.data.lot(lot))
        self.assert_response(
            response,
            "confirm_quantity",
            data=data,
            message=message,
        )

    def assert_response_set_quantity(self, response, move_line, message=None):
        self.assert_response(
            response,
            "set_quantity",
            data={"move_line": self.data.move_line(move_line)},
            message=message,
        )

    def assert_response_scan_destination_location(
        self, response, picking, move_lines, message=None
    ):
        self.assert_response(
            response,
            "scan_destination_location",
            data={
                "picking": self.data.picking(picking),
                "move_lines": self.data.move_lines(move_lines),
            },
            message=message,
        )
