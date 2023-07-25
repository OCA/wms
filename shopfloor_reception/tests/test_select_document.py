# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from freezegun import freeze_time

from odoo import fields

from .common import CommonCase

_TODAY = "2022-12-07"
_TOMORROW = "2022-12-08"


class TestSelectDocument(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.tracking = "lot"

    def test_scan_barcode_not_found(self):
        # next step is select_document, with an error message
        response = self.service.dispatch("scan_document", params={"barcode": "NOPE"})
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_picking_name(self):
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": picking.name}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )

    def test_scan_picking_origin_multiple_pickings(self):
        # Multiple pickings with this origin are found.
        # Return the filtered list of pickings.
        picking_1 = self._create_picking()
        picking_2 = self._create_picking()
        pickings = picking_1 | picking_2
        pickings = pickings.sorted(lambda p: (p.scheduled_date, p.id), reverse=False)
        pickings.write({"origin": "Somewhere together"})
        response = self.service.dispatch(
            "scan_document", params={"barcode": "Somewhere together"}
        )
        message = (
            "This source document is part of multiple transfers, please scan a package."
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(pickings)},
            message={
                "message_type": "warning",
                "body": message,
            },
        )

    @freeze_time(_TODAY)
    def test_scan_picking_origin_multiple_pickings_one_today(self):
        # Multiple pickings with this origin are found,
        # but only one is due today.
        # Select that one and move to the next screen.
        picking_today = self._create_picking(scheduled_date=_TODAY)
        picking_tomorrow = self._create_picking(scheduled_date=_TOMORROW)
        pickings = picking_today | picking_tomorrow
        pickings = pickings.sorted(lambda p: (p.scheduled_date, p.id), reverse=False)
        pickings.write({"origin": "Somewhere together"})
        response = self.service.dispatch(
            "scan_document", params={"barcode": "Somewhere together"}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking_today),
        )

    def test_scan_picking_origin_one_picking(self):
        # Only 1 picking with this origin is found.
        # Move to select_move.
        picking = self._create_picking()
        picking.write({"origin": "Somewhere"})
        response = self.service.dispatch(
            "scan_document", params={"barcode": "Somewhere"}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )

    def test_scan_packaging_multiple_pickings(self):
        # next step is select_document, with documents filtered based on the product
        p1 = self._create_picking()
        p2 = self._create_picking()
        self._add_package(p1)
        self._add_package(p2)
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a_packaging.barcode}
        )
        body = "Several transfers found, please select a transfer manually."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(p1 | p2)},
            message={"message_type": "error", "body": body},
        )

    def test_scan_product_multiple_pickings(self):
        # next step is select_document, with documents filtered based on the packaging
        p1 = self._create_picking()
        p2 = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a.barcode}
        )
        body = "Several transfers found, please select a transfer manually."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(p1 | p2)},
            message={"message_type": "error", "body": body},
        )

    def test_scan_product_no_picking(self):
        # next_step is select_document, with an error message
        picking = self._create_picking()
        picking.write({"scheduled_date": fields.Datetime.today()})
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_c.barcode}
        )
        message = self.service.msg_store.product_not_found_in_pickings()
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking)},
            message=message,
        )

    def test_scan_packaging_no_picking(self):
        # next step is select_document, with an error message
        picking = self._create_picking()
        picking.write({"scheduled_date": fields.Datetime.today()})
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_c_packaging.barcode}
        )
        message = self.service.msg_store.product_not_found_in_pickings()
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking)},
            message=message,
        )
