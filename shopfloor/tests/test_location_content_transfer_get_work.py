# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .test_location_content_transfer_base import LocationContentTransferCommonCase

# pylint: disable=missing-return


class TestLocationContentTransferGetWork(LocationContentTransferCommonCase):
    """Tests for getting work

    Endpoints:

    * /find_work
    * /cancel_work
    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.menu.sudo().allow_get_work = True
        cls.pickings = cls.env["stock.picking"].search(
            [("location_id", "=", cls.stock_location.id)]
        )
        cls.move_lines = cls.pickings.move_line_ids.filtered(
            lambda line: line.qty_done == 0
            and line.state in ("assigned", "partially_available")
            and not line.shopfloor_user_id
        )
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls.content_loc2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Content Location 2",
                    "barcode": "Content2",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        cls._fill_stock_for_moves(
            picking1.move_ids, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_ids[0], location=cls.content_loc2)
        cls._fill_stock_for_moves(picking2.move_ids[1], location=cls.content_loc)
        cls.pickings.action_assign()

    def _get_location_lines(self, location):
        return self.env["stock.move.line"].search([("location_id", "=", location.id)])

    def test_get_work(self):
        """Check the first state is get_work when the option is enabled."""
        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response(
            response,
            next_state="get_work",
            data={},
        )

    def test_find_work_no_work_found(self):
        """Check the user asked for work but none is found."""
        # Cancel all moves related to the location we work from
        self.pickings.move_ids.filtered(lambda r: r.state != "done")._action_cancel()
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="get_work",
            data={},
            message=self.service.msg_store.no_work_found(),
        )

    def test_find_work_work_found(self):
        """Check the user is offered a location to work from."""
        next_location = self.service._find_location_to_work_from()
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="scan_location",
            data={
                "location": self.data.location(next_location),
            },
        )
        lines = self._get_location_lines(next_location)
        self.assertEqual(lines.shopfloor_user_id, self.env.user)
        # Confirm the location
        response = self.service.dispatch(
            "scan_location", params={"barcode": next_location.name}
        )
        self.assertEqual(response["next_state"], "scan_destination_all")

    def test_cancel_work(self):
        next_location = self.service._find_location_to_work_from()
        stock = self.service._actions_for("stock")
        location_lines = self._get_location_lines(next_location)
        stock.mark_move_line_as_picked(location_lines, quantity=0)
        location_lines = self._get_location_lines(next_location)
        self.assertEqual(location_lines.shopfloor_user_id, self.env.user)
        response = self.service.dispatch(
            "cancel_work", params={"location_id": next_location.id}
        )
        self.assert_response(
            response,
            next_state="get_work",
            data={},
            message={},
        )
        lines = self._get_location_lines(next_location)
        self.assertFalse(lines.shopfloor_user_id)
