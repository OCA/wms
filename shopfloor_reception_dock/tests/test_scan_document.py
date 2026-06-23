# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestScanDocument(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dock_0, cls.dock_1, cls.dock_2 = (
            cls.env["stock.dock"]
            .sudo()
            .create(
                [
                    {"name": "Dock 00", "barcode": "TEST-DOCK00"},
                    {"name": "Dock 01", "barcode": "TEST-DOCK01"},
                    {"name": "Dock 02", "barcode": "TEST-DOCK02"},
                ]
            )
        )

        cls.pick_1 = cls._create_picking()
        cls.pick_2_a = cls._create_picking()
        cls.pick_2_b = cls._create_picking()

        cls.pick_1.dock_ids = [Command.set(cls.dock_1.ids)]
        cls.pick_2_a.dock_ids = [Command.set(cls.dock_2.ids)]
        cls.pick_2_b.dock_ids = [Command.set(cls.dock_2.ids)]

    def test_scan_document_by_dock_no_picking(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.dock_0.barcode}
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={
                "pickings": self._data_for_pickings(
                    self.pick_1 | self.pick_2_a | self.pick_2_b
                )
            },
            message=self.msg_store.dock_no_assigned_picking(self.dock_0),
        )

    def test_scan_document_by_dock_one_picking(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.dock_1.barcode}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(self.pick_1)},
        )

    def test_scan_document_by_dock_multiple_pickings(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.dock_2.barcode}
        )
        self.assert_response(
            response,
            next_state="select_document",
            message=self.msg_store.dock_pickings_filtered(self.dock_2),
            data={"pickings": self._data_for_pickings(self.pick_2_a | self.pick_2_b)},
        )
