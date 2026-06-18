# Copyright 2026 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from .common import CommonCase


class TestFindWork(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menu.sudo().allow_get_work = True
        cls.location_src_a = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Source A",
                    "location_id": cls.location_src.id,
                }
            )
        )
        cls.location_src_b = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Source B",
                    "location_id": cls.location_src.id,
                }
            )
        )
        cls.product = cls.product_a
        cls._add_stock_to_product(cls.product_a, cls.location_src_a, 10)
        cls._add_stock_to_product(cls.product_b, cls.location_src_b, 10)
        cls.picking_1 = cls._create_picking(lines=[(cls.product_a, 10)])
        cls.picking_2 = cls._create_picking(lines=[(cls.product_b, 10)])

    def test_find_work(self):
        response = self.service.dispatch("find_work")
        data = {
            "move_line": self._data_for_move_line(
                fields.first(self.picking_1.move_line_ids)
            )
        }
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
        )

        # cancel select product to go back to find_work
        response = self.service.dispatch("scan_product__action_cancel")
        self.assert_response(
            response,
            next_state="get_work",
        )

        # cancel the first picking
        self.picking_1.action_cancel()
        response = self.service.dispatch("find_work")
        data = {
            "move_line": self._data_for_move_line(
                fields.first(self.picking_2.move_line_ids)
            )
        }
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
        )

    def test_confirm_start_line_line_not_found(self):
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": 0, "barcode": "whatever"},
        )
        self.assert_response(
            response,
            next_state="get_work",
            message=self.msg_store.record_not_found(),
        )

    def test_confirm_start_line_barcode_not_found(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": "NOPE"},
        )
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.barcode_not_found(),
        )

    def test_confirm_start_line_scan_product(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_confirm_start_line_scan_wrong_product(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_b.barcode,
            },
        )
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.wrong_record(self.product_b),
        )

    def test_confirm_start_line_scan_product_tracked_by_lot(self):
        self._set_product_tracking_by_lot(self.product_a)
        lot = self._create_lot_for_product(self.product_a, "LOT001")
        self._add_stock_to_product(self.product_a, self.location_src, 5, lot=lot)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
        )

    def test_confirm_start_line_scan_packaging(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_confirm_start_line_scan_lot(self):
        self._set_product_tracking_by_lot(self.product_a)
        lot = self._create_lot_for_product(self.product_a, "LOT001")
        self._add_stock_to_product(self.product_a, self.location_src, 5, lot=lot)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_confirm_start_line_scan_wrong_lot(self):
        self._set_product_tracking_by_lot(self.product_a)
        lot = self._create_lot_for_product(self.product_a, "LOT001")
        wrong_lot = self._create_lot_for_product(self.product_a, "LOT_WRONG")
        self._add_stock_to_product(self.product_a, self.location_src, 5, lot=lot)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": wrong_lot.name},
        )
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.wrong_record(wrong_lot),
        )

    def test_confirm_start_line_scan_package(self):
        package = self._create_empty_package("PKG001")
        self._add_stock_to_product(
            self.product_a, self.location_src_a, 5, package=package
        )
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        self.assertEqual(move_line.package_id, package)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": package.name},
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_confirm_start_line_scan_wrong_package(self):
        package = self._create_empty_package("PKG001")
        wrong_package = self._create_empty_package("PKG_WRONG")
        self._add_stock_to_product(
            self.product_a, self.location_src_a, 5, package=package
        )
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": wrong_package.name},
        )
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.wrong_record(wrong_package),
        )
