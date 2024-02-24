# Copyright 2024 Foodles (https://www.foodles.co)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.stock_service_level.tests.common import StockServiceLeveLCommonCase


class TestPropagateServiceLevel(StockServiceLeveLCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pick_ship_no_restriction_route = cls.pick_ship_route
        cls.pick_ship_no_restriction_route.name = "Any (with or without) service level"
        cls.pick_ship_no_restriction_route.service_level_selectable = False
        cls.pick_ship_no_restriction_route.sequence = 100
        cls.pick_ship_no_service_level_route = cls.pick_ship_no_restriction_route.copy(
            {
                "name": "Without service level only",
                "service_level_selectable": True,
                "sequence": 10,
            }
        )
        cls.pick_ship_std_route = cls.pick_ship_no_restriction_route.copy(
            {
                "name": "standard",
                "service_level_selectable": True,
                "sequence": 20,
            }
        )
        cls.pick_ship_prm_route = cls.pick_ship_no_restriction_route.copy(
            {
                "name": "premium",
                "service_level_selectable": True,
                "sequence": 30,
            }
        )
        cls.pick_ship_both_route = cls.pick_ship_no_restriction_route.copy(
            {
                "name": "both",
                "service_level_selectable": True,
                "sequence": 40,
            }
        )

        # cls.pick_ship_no_service_level_route.service_level_ids = False
        cls.pick_ship_std_route.service_level_ids = cls.service_level_std
        cls.pick_ship_prm_route.service_level_ids = cls.service_level_premium
        cls.pick_ship_both_route.service_level_ids = (
            cls.service_level_std | cls.service_level_premium
        )

        cls.product.categ_id.route_ids |= (
            cls.pick_ship_std_route
            | cls.pick_ship_prm_route
            | cls.pick_ship_both_route
            | cls.pick_ship_no_service_level_route
        )
        cls.location_3 = cls.env["stock.location"].create(
            {"name": "loc3: somewhere (not direct child of stock)"}
        )
        cls.premium_picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Premium transfer",
                "code": "internal",
                "sequence_code": "WH/PRM",
                "warehouse_id": cls.warehouse.id,
                "default_location_src_id": cls.location_3.id,
                "default_location_dest_id": cls.warehouse.wh_output_stock_loc_id.id,
            }
        )
        cls.prm_pick_rule = cls.pick_ship_prm_route.rule_ids.filtered(
            lambda r: r.location_src_id == cls.warehouse.lot_stock_id
        )
        cls.prm_pick_rule.picking_type_id = cls.premium_picking_type
        cls.prm_pick_rule.location_src_id = cls.location_3

        cls.location_4 = cls.env["stock.location"].create(
            {"name": "loc4: somewhere else used by the 'both' route"}
        )
        cls.both_picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "both: Std and Premium transfer",
                "code": "internal",
                "sequence_code": "WH/BOTH",
                "warehouse_id": cls.warehouse.id,
                "default_location_src_id": cls.location_4.id,
                "default_location_dest_id": cls.warehouse.wh_output_stock_loc_id.id,
            }
        )
        cls.both_pick_rule = cls.pick_ship_both_route.rule_ids.filtered(
            lambda r: r.location_src_id == cls.warehouse.lot_stock_id
        )
        cls.both_pick_rule.picking_type_id = cls.both_picking_type
        cls.both_pick_rule.location_src_id = cls.location_4

    def test_stock_service_level_rule_1(self):
        """Request 15 units sdt and 5 premium

        All routes are available with priority to std and prm routes

        expected result:

        loc 1  -- pick std 15 --\
                                 > -- delivery --
        loc 3  -- pick prm 5  --/

        Two route has been selected, as procurement group and picking
        type of both route are the same for delivery, moves are present
        in the same picking.
        """

        self._update_product_stock(10, location=self.location_1)
        self._update_product_stock(10, location=self.location_2)
        self._update_product_stock(10, location=self.location_3)
        self._update_product_stock(10, location=self.location_4)

        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    15,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_std.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_premium.id,
                    },
                ),
            ]
        )

        transfers = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )

        self.assertEqual(
            len(transfers),
            # Premium route and Standard route share the same picking type
            # and procurement group so they are in the same delivery picking
            # They don't share the same route so each picking the related
            # picking type
            3,
            transfers.move_lines.mapped(
                lambda move: (
                    move.rule_id.name,
                    move.picking_id.name,
                )
            ),
        )
        standard_picking = transfers.filtered(
            lambda pick: pick.picking_type_id.code == "internal"
            and pick.picking_type_id != self.premium_picking_type
        )
        premium_picking = transfers.filtered(
            lambda pick: pick.picking_type_id == self.premium_picking_type
        )
        self.assertEqual(
            standard_picking.move_lines.rule_id.route_id,
            self.pick_ship_std_route,
        )
        self.assertEqual(
            premium_picking.move_lines.rule_id.route_id,
            self.pick_ship_prm_route,
        )
        premium_picking.action_assign()
        standard_picking.action_assign()

        def assert_move_line_per_location(
            moves,
            expect_from_location,
            expected_service_level,
            expect_reserved_qty,
        ):
            concern_move_line = moves.filtered(
                lambda mov: mov.location_id == expect_from_location
                and mov.move_id.service_level_id == expected_service_level
            )
            self.assertEqual(len(concern_move_line), 1)
            self.assertEqual(concern_move_line.product_uom_qty, expect_reserved_qty)

        assert_move_line_per_location(
            premium_picking.move_line_ids,
            self.location_3,
            self.service_level_premium,
            5,
        )
        assert_move_line_per_location(
            standard_picking.move_line_ids, self.location_1, self.service_level_std, 10
        )
        assert_move_line_per_location(
            standard_picking.move_line_ids, self.location_2, self.service_level_std, 5
        )

    def test_stock_service_level_rule_2(self):
        """Request 15 units sdt and 5 premium

        All routes are available with priority to the non restrictive
        routes

        expected result:

        loc 1/2  -- pick 10 + 5 + 5 -- delivery --

        One route has been selected.
        """
        self.pick_ship_no_restriction_route.sequence = 1

        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    10,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_std.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_premium.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": False,
                    },
                ),
            ]
        )

        transfers = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )

        self.assertEqual(
            len(transfers),
            2,
            transfers.move_lines.mapped(
                lambda move: (
                    move.rule_id.name,
                    move.picking_id.name,
                )
            ),
        )
        picking = transfers.filtered(
            lambda pick: pick.picking_type_id.code == "internal"
        )

        self.assertEqual(
            len(picking.move_lines),
            3,
        )
        self.assertEqual(
            picking.move_lines.rule_id.route_id,
            self.pick_ship_no_restriction_route,
            f"Got {picking.move_lines.rule_id.route_id.name} "
            f"expected {self.pick_ship_no_restriction_route.name} route.",
        )

    def test_stock_service_level_rule_3(self):
        """Request 15 units sdt and 5 premium

        All routes are available with priority to the 'both' routes

        expected result:

        loc 4  -- pick both 15 + 5 --> -- delivery --

        One route has been selected.
        """
        self.pick_ship_both_route.sequence = 1

        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    15,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_std.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_premium.id,
                    },
                ),
            ]
        )

        transfers = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )

        self.assertEqual(
            len(transfers),
            2,
            transfers.move_lines.mapped(
                lambda move: (
                    move.rule_id.name,
                    move.picking_id.name,
                )
            ),
        )
        picking = transfers.filtered(
            lambda pick: pick.picking_type_id.code == "internal"
        )

        self.assertEqual(
            len(picking.move_lines),
            2,
        )
        self.assertEqual(
            picking.move_lines.rule_id.route_id,
            self.pick_ship_both_route,
        )

    def test_stock_service_level_rule_4(self):
        """Request 15 units without service level

        All routes are available with the lowest priority to the
        non no service level route which is expected to be selected

        expected result:

        loc 1/2  -- pick 15 + 5 in one move -- delivery --

        """
        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    15,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                    },
                ),
            ]
        )

        transfers = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )

        self.assertEqual(
            len(transfers),
            2,
            transfers.move_lines.mapped(
                lambda move: (
                    move.rule_id.name,
                    move.picking_id.name,
                )
            ),
        )
        picking = transfers.filtered(
            lambda pick: pick.picking_type_id.code == "internal"
        )

        self.assertEqual(
            len(picking.move_lines),
            1,
        )
        self.assertEqual(
            picking.move_lines.rule_id.route_id,
            self.pick_ship_no_service_level_route,
            f"Got {picking.move_lines.rule_id.route_id.name} "
            f"(seq: {picking.move_lines.rule_id.route_id.sequence}) "
            f"expected {self.pick_ship_no_service_level_route.name} "
            f"(seq: {self.pick_ship_no_service_level_route.sequence}) route.",
        )

    def test_stock_service_level_rule_5(self):
        """Request 15 units sdt and 5 premium

        Std routes is not available fall back on both, prm is still
        the first

        expected result:

        loc 4  -- pick both 15 --\
                                 > -- delivery --
        loc 3  -- pick prm 5  --/

        Two route has been selected, as procurement group and picking
        type of both route are the same for delivery, moves are present
        in the same picking.
        """
        self.product.categ_id.route_ids -= self.pick_ship_std_route
        self._update_product_stock(10, location=self.location_1)
        self._update_product_stock(10, location=self.location_2)
        self._update_product_stock(10, location=self.location_3)
        self._update_product_stock(15, location=self.location_4)

        procurement_group = self.env["procurement.group"].create(
            {"name": "My procurement", "move_type": "one"}
        )
        self.env["procurement.group"].run(
            [
                self.env["procurement.group"].Procurement(
                    self.product,
                    15,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin standard service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_std.id,
                    },
                ),
                self.env["procurement.group"].Procurement(
                    self.product,
                    5,
                    self.product.uom_id,
                    self.customer_loc,
                    "a name",
                    "an origin premium service level",
                    self.env.company,
                    {
                        "group_id": procurement_group,
                        "service_level_id": self.service_level_premium.id,
                    },
                ),
            ]
        )

        transfers = self.env["stock.picking"].search(
            [("group_id", "=", procurement_group.id)]
        )

        self.assertEqual(
            len(transfers),
            # Premium route and Standard route share the same picking type
            # and procurement group so they are in the same delivery picking
            # They don't share the same route so each picking the related
            # picking type
            3,
            transfers.move_lines.mapped(
                lambda move: (
                    move.rule_id.name,
                    move.picking_id.name,
                )
            ),
        )
        standard_picking_by_both_route = transfers.filtered(
            lambda pick: pick.picking_type_id.code == "internal"
            and pick.picking_type_id != self.premium_picking_type
        )
        premium_picking = transfers.filtered(
            lambda pick: pick.picking_type_id == self.premium_picking_type
        )
        self.assertEqual(
            standard_picking_by_both_route.move_lines.rule_id.route_id,
            self.pick_ship_both_route,
        )
        self.assertEqual(
            premium_picking.move_lines.rule_id.route_id,
            self.pick_ship_prm_route,
        )
        premium_picking.action_assign()
        standard_picking_by_both_route.action_assign()

        def assert_move_line_per_location(
            moves,
            expect_from_location,
            expected_service_level,
            expect_reserved_qty,
        ):
            concern_move_line = moves.filtered(
                lambda mov: mov.location_id == expect_from_location
                and mov.move_id.service_level_id == expected_service_level
            )
            self.assertEqual(len(concern_move_line), 1)
            self.assertEqual(concern_move_line.product_uom_qty, expect_reserved_qty)

        assert_move_line_per_location(
            premium_picking.move_line_ids,
            self.location_3,
            self.service_level_premium,
            5,
        )
        assert_move_line_per_location(
            standard_picking_by_both_route.move_line_ids,
            self.location_4,
            self.service_level_std,
            15,
        )
