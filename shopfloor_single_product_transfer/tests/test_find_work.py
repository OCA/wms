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
        # Simulate putaway rules having run so that no_putaway_available returns
        # False for the class-level pickings. Without this, find_work would
        # return no_putaway_destination_available for every test.
        cls.picking_1.move_line_ids.sudo().location_dest_id = cls.dispatch_location.id
        cls.picking_2.move_line_ids.sudo().location_dest_id = cls.dispatch_location.id

    def _data_for_start_line(
        self, move_line, selected_location_id=None, selected_package_id=None
    ):
        return {
            "move_line": self._data_for_move_line(move_line),
            "selected_location_id": selected_location_id,
            "selected_package_id": selected_package_id,
            "scan_location_or_pack_first": self.menu.scan_location_or_pack_first,
        }

    def _setup_lot_move_line(self, location=None):
        location = location or self.location_src
        self._set_product_tracking_by_lot(self.product_a)
        lot = self._create_lot_for_product(self.product_a, "LOT001")
        self._add_stock_to_product(self.product_a, location, 5, lot=lot)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        return move_line, lot

    def _assert_start_line_lot_required(
        self, response, move_line, selected_location_id=None
    ):
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(
                move_line, selected_location_id=selected_location_id
            ),
            message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
        )

    def _assert_set_quantity(self, response, move_line):
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "move_line": self._data_for_move_line(move_line),
                "asking_confirmation": None,
            },
        )

    def test_find_work(self):
        response = self.service.dispatch("find_work")
        data = self._data_for_start_line(fields.first(self.picking_1.move_line_ids))
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
        data = self._data_for_start_line(fields.first(self.picking_2.move_line_ids))
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
        data = self._data_for_start_line(move_line)
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
        self._assert_set_quantity(response, move_line)

    def test_confirm_start_line_scan_wrong_product(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_b.barcode,
            },
        )
        data = self._data_for_start_line(move_line)
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
        self._assert_start_line_lot_required(response, move_line)

    def test_confirm_start_line_scan_packaging(self):
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self._assert_set_quantity(response, move_line)

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
        self._assert_set_quantity(response, move_line)

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
        data = self._data_for_start_line(move_line)
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
        self._assert_set_quantity(response, move_line)

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
        data = self._data_for_start_line(move_line)
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.wrong_record(wrong_package),
        )

    def _enable_scan_location_or_pack_first(self):
        self.menu.sudo().scan_location_or_pack_first = True

    def _setup_packaged_move_line(self):
        package = self._create_empty_package("PKG001")
        self._add_stock_to_product(
            self.product_a, self.child_location, 5, package=package
        )
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        return move_line, package

    def test_confirm_start_line_slpf_scan_product_requires_location(self):
        self._enable_scan_location_or_pack_first()
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        data = self._data_for_start_line(move_line)
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.scan_the_location_first(),
        )

    def test_confirm_start_line_scan_slpf_scan_location(self):
        self._enable_scan_location_or_pack_first()
        self._add_stock_to_product(self.product_a, self.child_location, 5)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_confirm_start_line_scan_slpf_lot_tracked_scan_location(self):
        # With scan_location_or_pack_first, scanning the location on a
        # lot-tracked line is sufficient to confirm: goes to set_quantity
        # directly, bypassing the lot scan step.
        self._enable_scan_location_or_pack_first()
        self._set_product_tracking_by_lot(self.product_a)
        lot = self._create_lot_for_product(self.product_a, "LOT001")
        self._add_stock_to_product(self.product_a, self.child_location, 5, lot=lot)
        picking = self._create_picking(lines=[(self.product_a, 5)])
        move_line = fields.first(picking.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=self.child_location.id
        )

    def test_confirm_start_line_scan_slpf_scan_product_with_location(
        self,
    ):
        self._enable_scan_location_or_pack_first()
        move_line = fields.first(self.picking_1.move_line_ids)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
                "selected_location_id": move_line.location_id.id,
            },
        )
        self._assert_set_quantity(response, move_line)

    def test_confirm_start_line_slpf_package_scan_product_requires_package(self):
        self._enable_scan_location_or_pack_first()
        move_line, _package = self._setup_packaged_move_line()
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        data = self._data_for_start_line(move_line)
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.line_has_package_scan_package(),
        )

    def test_confirm_start_line_slpf_package_scan_location_requires_package(self):
        self._enable_scan_location_or_pack_first()
        move_line, _package = self._setup_packaged_move_line()
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        data = self._data_for_start_line(
            move_line, selected_location_id=self.child_location.id
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=data,
            message=self.msg_store.line_has_package_scan_package(),
        )

    def test_confirm_start_line_scan_slpf_package_scan_package(
        self,
    ):
        self._enable_scan_location_or_pack_first()
        move_line, package = self._setup_packaged_move_line()
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": package.name},
        )
        self._assert_set_quantity(response, move_line)

    # -------------------------------------------------------------------------
    # Lot tracking: all paths that require a lot must stay on start_line,
    # and scanning the lot must reach set_quantity.
    # -------------------------------------------------------------------------

    # -- Without scan_location_or_pack_first --

    def test_confirm_start_line_lot_tracked_scan_location_requires_lot(self):
        move_line, _lot = self._setup_lot_move_line(self.child_location)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=self.child_location.id
        )

    def test_confirm_start_line_lot_tracked_scan_packaging_requires_lot(self):
        move_line, _lot = self._setup_lot_move_line()
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self._assert_start_line_lot_required(response, move_line)

    def test_confirm_start_line_lot_tracked_scan_product_then_lot(self):
        move_line, lot = self._setup_lot_move_line()
        # Step 1: product scan -> lot required
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self._assert_start_line_lot_required(response, move_line)
        # Step 2: lot scan -> set_quantity
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        self._assert_set_quantity(response, move_line)

    def test_confirm_start_line_lot_tracked_scan_location_then_lot(self):
        move_line, lot = self._setup_lot_move_line(self.child_location)
        # Step 1: location scan -> lot required
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=self.child_location.id
        )
        # Step 2: lot scan -> set_quantity (no slpf, no location check needed)
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        self._assert_set_quantity(response, move_line)

    # -- With scan_location_or_pack_first --

    def test_confirm_start_line_slpf_lot_tracked_scan_lot_no_location(self):
        self._enable_scan_location_or_pack_first()
        move_line, lot = self._setup_lot_move_line()
        response = self.service.dispatch(
            "confirm_start_line",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line),
            message=self.msg_store.scan_the_location_first(),
        )

    def test_confirm_start_line_slpf_lot_tracked_product_with_location_requires_lot(
        self,
    ):
        self._enable_scan_location_or_pack_first()
        move_line, _lot = self._setup_lot_move_line()
        location_id = move_line.location_id.id
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
                "selected_location_id": location_id,
            },
        )
        # slpf check passes (location provided); lot still required
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=location_id
        )

    def test_confirm_start_line_slpf_lot_tracked_product_with_location_then_lot(self):
        self._enable_scan_location_or_pack_first()
        move_line, lot = self._setup_lot_move_line()
        location_id = move_line.location_id.id
        # Step 1: product + location -> lot required (location preserved in response)
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.product_a.barcode,
                "selected_location_id": location_id,
            },
        )
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=location_id
        )
        # Step 2: lot + location -> set_quantity
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": lot.name,
                "selected_location_id": location_id,
            },
        )
        self._assert_set_quantity(response, move_line)

    def test_confirm_start_line_slpf_lot_tracked_scan_location_then_lot(self):
        self._enable_scan_location_or_pack_first()
        move_line, lot = self._setup_lot_move_line(self.child_location)
        # Step 1: location scan -> lot required
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.child_location.barcode,
            },
        )
        self._assert_start_line_lot_required(
            response, move_line, selected_location_id=self.child_location.id
        )
        # Step 2: lot + location (frontend passes the confirmed location)
        # -> set_quantity
        response = self.service.dispatch(
            "confirm_start_line",
            params={
                "selected_line_id": move_line.id,
                "barcode": lot.name,
                "selected_location_id": self.child_location.id,
            },
        )
        self._assert_set_quantity(response, move_line)

    # -------------------------------------------------------------------------
    # ignore_no_putaway_available flag behaviour in find_work
    # -------------------------------------------------------------------------

    def test_find_work_no_putaway_destination(self):
        # With ignore_no_putaway_available=False (default), find_work returns
        # an error and stays at get_work when the candidate line has no
        # putaway destination (location_dest_id == picking type default).
        self.picking_1.action_cancel()
        self.picking_2.action_cancel()
        self._add_stock_to_product(self.product_a, self.location_src_a, 3)
        self._create_picking(lines=[(self.product_a, 3)])
        response = self.service.dispatch("find_work")
        self.assert_response(
            response,
            next_state="get_work",
            message=self.msg_store.no_putaway_destination_available(),
        )

    def test_find_work_ignore_no_putaway_skips_to_next(self):
        # With ignore_no_putaway_available=True, lines without a specific
        # putaway destination are skipped; the next eligible line is returned.
        self._enable_ignore_no_putaway_available()
        default_dest = self.picking_1.picking_type_id.default_location_dest_id
        self.picking_1.move_line_ids.sudo().location_dest_id = default_dest.id
        # picking_2 still has dispatch_location as destination (set in setUpClass)
        response = self.service.dispatch("find_work")
        move_line = fields.first(self.picking_2.move_line_ids)
        self.assert_response(
            response,
            next_state="start_line",
            data=self._data_for_start_line(move_line),
        )

    def test_find_work_ignore_no_putaway_no_work_found(self):
        # With ignore_no_putaway_available=True, if every candidate line has no
        # putaway destination, find_work returns no_work_found.
        self._enable_ignore_no_putaway_available()
        self.picking_1.action_cancel()
        self.picking_2.action_cancel()
        self._add_stock_to_product(self.product_a, self.location_src_a, 3)
        self._create_picking(lines=[(self.product_a, 3)])
        response = self.service.dispatch("find_work")
        self.assert_response(
            response,
            next_state="get_work",
            message=self.msg_store.no_work_found(),
        )
