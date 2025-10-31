# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestReceptionHelpdesk(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PickingType = cls.env["stock.picking.type"].sudo()
        cls.suppliers = cls.env.ref("stock.stock_location_suppliers")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.Product = cls.env["product.product"].sudo()
        cls.purchase_team = (
            cls.env["helpdesk.ticket.team"].sudo().create({"name": "Purchase Helpdesk"})
        )

        cls.type_rec = cls.PickingType.create(
            {
                "name": "Reception Test",
                "sequence_code": "REC-TEST",
                "allow_helpdesk_ticket": True,
                "default_helpdesk_team_id": cls.purchase_team.id,
            }
        )
        cls.env.user.groups_id |= cls.env.ref("helpdesk_mgmt.group_helpdesk_user")

    def test_set_done_backorder_urgent(self):
        self.menu.sudo().picking_type_ids = self.type_rec
        picking = self._create_picking(picking_type=self.type_rec)
        line = picking.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertFalse(line.move_id.helpdesk_ticket_ids)
        response = self.service.dispatch(
            "start_helpdesk",
            params={"picking_id": picking.id, "selected_line_id": line.id},
        )

        self.assertEqual(
            response["data"]["start_helpdesk"]["selected_move_line"],
            self.data.move_lines(line),
        )
        self.assertEqual(
            response["data"]["start_helpdesk"]["picking"], self.data.picking(picking)
        )

        response = self.service.dispatch(
            "create_helpdesk",
            params={
                "picking_id": picking.id,
                "selected_line_id": line.id,
                "description": "Test Helpdesk",
            },
        )
        self.assertTrue(line.move_id.helpdesk_ticket_ids)
        message = f"Helpdesk ticket ({line.move_id.helpdesk_ticket_ids.display_name}) created!"
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": self._data_for_picking(picking, with_progress=False),
                "selected_move_line": self.data.move_lines(line),
            },
            message={
                "body": message,
                "message_type": "success",
            },
        )
