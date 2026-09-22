# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)

# pylint: disable=missing-return


class TestLocationContentTransferGetWork(LocationContentTransferCommonCase):
    """Tests for deferred putaway recomputation triggered by the 'Get Work' action.

    Context
    -------
    The picking type is configured with ``defer_putaway_to_operator = True``.
    Putaway strategies are **skipped at reservation time** for all move lines
    (including those that move a whole package via ``package_level_id``).
    Those lines are flagged ``putaway_deferred = True`` and their
    ``location_dest_id`` stays at the move's generic destination until the
    operator presses 'Get Work', which triggers the actual computation.

    Only lines whose ``result_package_id`` is a *new* package being filled
    during the operation (no ``package_level_id``) are excluded from the
    deferred mechanism: the operator sets that destination explicitly and it
    must never be overridden automatically.

    If the operator manually sets a destination on any line (or package level),
    the ``write`` override clears ``putaway_deferred`` immediately, so the
    mechanism will never override an operator-set destination.

    Fixture
    -------
    Two pickings under the Location Content Transfer operation type (default
    source and destination: ``stock_location`` / WH/Stock):

    - **picking1** – product_a × 10 and product_b × 10, stock in **packages**
      at ``content_loc``.  Lines have ``package_level_id`` set, so they are
      included in the deferred mechanism (``putaway_deferred = True``).

    - **picking2** – product_c × 10 at ``content_loc2`` (loose) and
      product_d × 10 at ``content_loc`` (loose).  Same deferred behavior.

    Putaway rules route all four products to ``shelf1`` when goods arrive at
    ``stock_location``.
    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.menu.sudo().allow_get_work = True
        cls.picking_type.sudo().allow_to_recompute_putaways = True
        cls.picking_type.sudo().defer_putaway_to_operator = True
        cls.pickings = cls.env["stock.picking"].search(
            [("location_id", "=", cls.stock_location.id)]
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

    def test_find_work_package_line_putaway_applied(self):
        """Package move lines are deferred and their destination updated at 'Get Work'.

        Scenario
        --------
        picking1's lines move a whole existing package (``package_level_id``
        is set, ``result_package_id == package_id``).  With
        ``defer_putaway_to_operator = True``, putaway is **skipped** at
        reservation: ``putaway_deferred = True`` and ``location_dest_id``
        stays at ``stock_location`` (the move's generic destination).

        After reservation the putaway rule for product_a and product_b
        is changed to route to ``shelf2`` instead of ``shelf1``.

        When the operator presses 'Get Work', the deferred putaway is
        recomputed using the **current** rule.  The destination of picking1's
        product_a and product_b lines is therefore updated to ``shelf2``.

        The test also verifies the full 'Get Work' → 'scan_location' flow and
        that all lines in the location are claimed by the current user.
        """
        next_location = self.service._find_location_to_work_from()
        # Putaway was deferred at reservation: destination is still the move's
        # generic destination, not yet routed to a shelf.
        self.assertEqual(
            self.picking1.move_line_ids[0].location_dest_id,
            self.picking_type.default_location_dest_id,
        )
        rules = self.env["stock.putaway.rule"].search(
            [("product_id", "in", (self.product_a.id, self.product_b.id))]
        )
        rules.sudo().location_out_id = self.shelf2
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="scan_location",
            data={
                "location": self.data.location(next_location),
            },
        )
        # Destination updated with the current rule (shelf2, not shelf1).
        self.assertEqual(self.picking1.move_line_ids.location_dest_id, self.shelf2)
        lines = self._get_location_lines(next_location)
        self.assertEqual(lines.shopfloor_user_id, self.env.user)
        # Confirm the location
        response = self.service.dispatch(
            "scan_location", params={"barcode": next_location.name}
        )
        self.assertEqual(response["next_state"], "start_single")

    def test_find_work_loose_line_putaway_applied(self):
        """Loose move lines are deferred and their destination updated at 'Get Work'.

        Scenario
        --------
        picking1's lines are loose (``result_package_id`` removed after
        reservation to simulate a loose-item transfer).  The destination is
        updated to reflect the **current** putaway rule when the operator
        presses 'Get Work', and the ``scan_location`` response propagates the
        new destination to the UI.
        """
        next_location = self.service._find_location_to_work_from()
        rule = self.env["stock.putaway.rule"].search(
            [("product_id", "=", self.product_a.id)]
        )
        rule.sudo().location_out_id = self.shelf2
        # Detach the package to obtain a loose move line.
        self.picking1.move_line_ids.result_package_id = False
        response = self.service.dispatch("find_work", params={})
        self.assert_response(
            response,
            next_state="scan_location",
            data={
                "location": self.data.location(next_location),
            },
        )
        # Destination updated with the current rule (shelf2).
        self.assertEqual(self.picking1.move_line_ids[0].location_dest_id, self.shelf2)

        # Boost priority so this line is the first one returned in scan_location.
        self.picking1.move_line_ids[0].shopfloor_priority = 1

        lines = self._get_location_lines(next_location)
        self.assertEqual(lines.shopfloor_user_id, self.env.user)
        response = self.service.dispatch(
            "scan_location", params={"barcode": next_location.name}
        )
        self.assertEqual(
            response.get("data")
            .get("start_single")
            .get("move_line")
            .get("location_dest")
            .get("id"),
            self.shelf2.id,
        )
