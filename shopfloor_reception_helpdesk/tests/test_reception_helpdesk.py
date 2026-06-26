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
        cls.other_team = (
            cls.env["helpdesk.ticket.team"].sudo().create({"name": "Other Team"})
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
        cls.motive = (
            cls.env["helpdesk.ticket.motive"]
            .sudo()
            .create({"name": "Test Motive", "team_id": cls.purchase_team.id})
        )
        cls.motive_no_team = (
            cls.env["helpdesk.ticket.motive"]
            .sudo()
            .create({"name": "Test Motive", "team_id": False})
        )
        cls.motive_other_team = (
            cls.env["helpdesk.ticket.motive"]
            .sudo()
            .create({"name": "Test Motive", "team_id": cls.other_team.id})
        )

    def _create_ticket_from_state(self, state, picking, line=None):
        response = self.service.dispatch(
            "start_helpdesk",
            params={
                "picking_id": picking.id,
                "selected_line_id": line.id if line else None,
                "state": state,
            },
        )
        start_helpdesk_data = response["data"]["start_helpdesk"]

        response = self.service.dispatch(
            "create_helpdesk",
            params={
                "picking_id": picking.id,
                "selected_line_id": line.id if line else None,
                "helpdesk_wizard_id": start_helpdesk_data["helpdesk_wizard"]["id"],
                "description": "Test Helpdesk",
                "motive_id": self.motive.id,
                "origin_state": state,
            },
        )

        return response

    def test_start_helpdesk(self):
        self.menu.sudo().picking_type_ids = self.type_rec
        picking = self._create_picking(picking_type=self.type_rec)
        line = picking.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertFalse(line.move_id.helpdesk_ticket_ids)

        response = self.service.dispatch(
            "start_helpdesk",
            params={
                "picking_id": picking.id,
                "selected_line_id": line.id,
                "state": "set_lot",
            },
        )

        # Ensure state data consistency
        start_helpdesk_data = response["data"]["start_helpdesk"]
        self.assertEqual(
            start_helpdesk_data["selected_move_line"],
            self.data.move_lines(line),
        )
        self.assertEqual(start_helpdesk_data["picking"], self.data.picking(picking))

        # Test only expected motives are visible in frontend
        available_motive_ids = [
            m["id"] for m in start_helpdesk_data["available_motives"]
        ]
        self.assertIn(self.motive_no_team.id, available_motive_ids)
        self.assertIn(self.motive.id, available_motive_ids)
        self.assertNotIn(self.motive_other_team.id, available_motive_ids)

    def test_create_ticket_from_set_quantity(self):
        self.menu.sudo().picking_type_ids = self.type_rec
        picking = self._create_picking(picking_type=self.type_rec)
        line = picking.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertFalse(line.move_id.helpdesk_ticket_ids)

        response = self._create_ticket_from_state("set_quantity", picking, line)

        helpdesk_ticket = line.move_id.helpdesk_ticket_ids
        self.assertTrue(helpdesk_ticket)
        self.assertEqual(helpdesk_ticket.motive_id, self.motive)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": self._data_for_picking(picking, with_progress=False),
                "selected_move_line": self.data.move_lines(line),
                "confirmation": None,
            },
            message=self.msg_store.helpdesk_ticket_created(helpdesk_ticket),
        )

    def test_create_ticket_from_set_lot(self):
        self.menu.sudo().picking_type_ids = self.type_rec
        picking = self._create_picking(picking_type=self.type_rec)
        line = picking.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        self.assertFalse(line.move_id.helpdesk_ticket_ids)

        response = self._create_ticket_from_state("set_lot", picking, line)

        helpdesk_ticket = line.move_id.helpdesk_ticket_ids
        self.assertTrue(helpdesk_ticket)
        self.assertEqual(helpdesk_ticket.motive_id, self.motive)
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
            message=self.msg_store.helpdesk_ticket_created(helpdesk_ticket),
        )

    def test_create_ticket_from_select_move(self):
        self.menu.sudo().picking_type_ids = self.type_rec
        picking = self._create_picking(picking_type=self.type_rec)
        self.assertFalse(picking.helpdesk_ticket_ids)

        response = self._create_ticket_from_state("select_move", picking)

        helpdesk_ticket = picking.helpdesk_ticket_ids
        self.assertTrue(helpdesk_ticket)
        self.assertEqual(helpdesk_ticket.motive_id, self.motive)
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
            message=self.msg_store.helpdesk_ticket_created(helpdesk_ticket),
        )
