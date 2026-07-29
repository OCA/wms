# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestScanDocument(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.pick_1 = cls._create_picking()
        cls.pick_2 = cls._create_picking()
        cls.pick_3 = cls._create_picking()

        cls.pickings = cls.pick_1 | cls.pick_2 | cls.pick_3

        cls.grn_no_picking = (
            cls.env["stock.grn"]
            .sudo()
            .create(
                {
                    "carrier_id": cls.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": "Test Carrier",
                        }
                    )
                    .id,
                    "delivery_note_supplier_number": "Test Supplier Note Nbr",
                }
            )
        )
        cls.grn_one_picking = cls.grn_no_picking.copy()
        cls.grn_one_picking.picking_ids = [Command.set(cls.pick_1.ids)]

        cls.grn_multiple_pickings = cls.grn_no_picking.copy()
        cls.grn_multiple_pickings.picking_ids = [
            Command.set((cls.pick_2 | cls.pick_3).ids)
        ]

    def test_scan_document_by_grn_no_picking(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.grn_no_picking.name}
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(self.pickings)},
            message=self.msg_store.no_picking_found_for_grn(self.grn_no_picking),
        )

    def test_scan_document_by_grn_one_picking(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.grn_one_picking.name}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data={
                "picking": self._data_for_picking_with_moves(
                    self.grn_one_picking.picking_ids
                )
            },
        )

    def test_scan_document_by_dock_multiple_pickings(self):
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.grn_multiple_pickings.name}
        )
        self.assert_response(
            response,
            next_state="select_document",
            message=self.msg_store.grn_pickings_filtered(self.grn_multiple_pickings),
            data={
                "pickings": self._data_for_pickings(
                    self.grn_multiple_pickings.picking_ids.sorted(lambda p: p.id)
                )
            },
        )
