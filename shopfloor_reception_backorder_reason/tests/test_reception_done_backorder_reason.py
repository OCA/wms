# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestReceptionBackorderReason(CommonCase):
    def _data_for_backorder_reasons(self, reasons):
        return self.data.backorder_reasons(reasons)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reason_urgent = cls.env.ref(
            "stock_picking_backorder_reason.stock_backorder_reason_urgent"
        )
        cls.reason_missing = cls.env.ref(
            "stock_picking_backorder_reason.stock_backorder_reason_missing"
        )
        cls.reason_never = cls.env.ref(
            "stock_picking_backorder_reason.stock_backorder_reason_never"
        )

        # Create a special Reception picking type (to avoid noise data)
        cls.in_type = (
            cls.env["stock.picking.type"]
            .sudo()
            .create(
                {
                    "name": "Receptions for Reasons",
                    "default_location_src_id": cls.env.ref(
                        "stock.stock_location_suppliers"
                    ).id,
                    "default_location_dest_id": cls.wh.lot_stock_id.id,
                    "sequence_code": "REC-BACK",
                    "backorder_reason": True,
                    "backorder_reason_purchase": True,
                }
            )
        )
        cls.reasons = cls.env["stock.backorder.reason"].search([])

    def test_set_done_backorder_urgent(self):
        self.menu.sudo().picking_type_ids = self.in_type
        picking = self._create_picking(picking_type=self.in_type)
        picking.move_line_ids.write({"qty_done": 5.0, "shopfloor_checkout_done": True})

        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        # User is asked to confirm the action
        self.assert_response(
            response,
            next_state="choose_backorder_reason",
            data={
                "backorder_reasons": self._data_for_backorder_reasons(self.reasons),
                "picking": self._data_for_picking(picking),
            },
            message=None,
        )
        response = self.service.dispatch(
            "choose_backorder_reason",
            params={
                "picking_id": picking.id,
                "reason_id": self.reason_urgent.id,
            },
        )
        picking_name = picking.name
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking.backorder_ids)},
            message={
                "body": f"Transfer {picking_name} done",
                "message_type": "success",
            },
        )
        self.assertEqual(picking.state, "done")

    def test_set_done_backorder_missing(self):
        self.menu.sudo().picking_type_ids = self.in_type
        picking = self._create_picking(picking_type=self.in_type)
        picking.partner_id.sudo().purchase_reason_backorder_strategy = "cancel"
        picking.move_line_ids.write({"qty_done": 5.0, "shopfloor_checkout_done": True})

        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        # User is asked to confirm the action
        self.assert_response(
            response,
            next_state="choose_backorder_reason",
            data={
                "backorder_reasons": self._data_for_backorder_reasons(self.reasons),
                "picking": self._data_for_picking(picking),
            },
            message=None,
        )
        response = self.service.dispatch(
            "choose_backorder_reason",
            params={
                "picking_id": picking.id,
                "reason_id": self.reason_missing.id,
            },
        )
        picking_name = picking.name
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "body": f"Transfer {picking_name} done",
                "message_type": "success",
            },
        )
        self.assertEqual(picking.state, "done")

    def test_set_done_backorder_never(self):
        self.menu.sudo().picking_type_ids = self.in_type
        picking = self._create_picking(picking_type=self.in_type)
        picking.partner_id.sudo().purchase_reason_backorder_strategy = "create"
        picking.move_line_ids.write({"qty_done": 5.0, "shopfloor_checkout_done": True})

        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        # User is asked to confirm the action
        self.assert_response(
            response,
            next_state="choose_backorder_reason",
            data={
                "backorder_reasons": self._data_for_backorder_reasons(self.reasons),
                "picking": self._data_for_picking(picking),
            },
            message=None,
        )
        response = self.service.dispatch(
            "choose_backorder_reason",
            params={
                "picking_id": picking.id,
                "reason_id": self.reason_never.id,
            },
        )
        picking_name = picking.name
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "body": f"Transfer {picking_name} done",
                "message_type": "success",
            },
        )
        self.assertEqual(picking.state, "done")

    def test_set_done_backorder_transparent_cancel(self):
        self.menu.sudo().picking_type_ids = self.in_type
        picking = self._create_picking(picking_type=self.in_type)
        self.in_type.sudo().backorder_reason_transparent_cancel = True
        picking.partner_id.sudo().purchase_reason_backorder_strategy = "cancel"
        picking.move_line_ids.write({"qty_done": 5.0, "shopfloor_checkout_done": True})

        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        picking_name = picking.name
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "body": f"Transfer {picking_name} done",
                "message_type": "success",
            },
        )
        self.assertEqual(picking.state, "done")
        self.assertFalse(picking.backorder_ids)

    def test_set_done_backorder_urgent_already_done(self):
        self.menu.sudo().picking_type_ids = self.in_type
        picking = self._create_picking(picking_type=self.in_type)
        picking.move_line_ids.write({"qty_done": 5.0, "shopfloor_checkout_done": True})

        picking._action_done()
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(picking)},
            message={"body": "Operation already processed.", "message_type": "info"},
        )
