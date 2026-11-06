# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_menu_base import MenuCountersCommonCase


class TestMenuCountersCommonCase(MenuCountersCommonCase):
    def test_menu_search_profile1(self):
        expected_counters = {
            self.menu1.id: {
                "lines_count": 2,
                "picking_count": 2,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
            self.menu2.id: {
                "lines_count": 6,
                "picking_count": 3,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
        }
        expected_menu_items = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile.id)])
        )
        # ensures expected counters are in the expected menu items
        self.assertIn(self.menu1, expected_menu_items)
        self.assertIn(self.menu2, expected_menu_items)
        service = self.get_service("menu", profile=self.wms_profile)
        response = service.dispatch("search")
        self._assert_menu_response(
            response,
            expected_menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )

    def test_menu_search_profile2(self):
        expected_menu_items = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile2.id)])
        )
        expected_counters = {
            expected_menu_item[0].id: {
                "lines_count": 0,
                "picking_count": 0,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            }
            for expected_menu_item in expected_menu_items
        }
        service = self.get_service("menu", profile=self.wms_profile2)
        response = service.dispatch("search")
        self._assert_menu_response(
            response,
            expected_menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )

    def test_menu_counter_priority(self):
        """Test that priority counters are correctly computed.

        Priority on lines must be based on the move priority.
        Priority on pickings must be based on the picking priority.
        """
        self.pickings.write({"priority": "0"})
        self.pickings.move_ids.write({"priority": "0"})
        pickings_menu_2 = self.pickings.filtered(
            lambda p: p.picking_type_id == self.menu2_picking_type
        )
        # Set priority on pickings only for first picking of menu 2
        pickings_menu_2[0].write({"priority": "1"})
        pickings_menu_2[0].move_ids.write({"priority": "0"})

        # set priority on move lines only for second picking of menu 2
        pickings_menu_2[1].write({"priority": "0"})
        pickings_menu_2[1].move_ids[0].write({"priority": "1"})

        # set priority on both move lines and pickings for third picking of menu 2
        pickings_menu_2[2].write({"priority": "1"})
        pickings_menu_2[2].move_ids.write({"priority": "1"})

        expected_counters = {
            self.menu1.id: {
                "lines_count": 2,
                "picking_count": 2,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
            self.menu2.id: {
                "lines_count": 6,
                "picking_count": 3,
                "priority_lines_count": 1 + len(pickings_menu_2[2].move_ids),
                "priority_picking_count": 2,
            },
        }
        expected_menu_items = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile.id)])
        )
        # ensures expected counters are in the expected menu items
        self.assertIn(self.menu1, expected_menu_items)
        self.assertIn(self.menu2, expected_menu_items)
        service = self.get_service("menu", profile=self.wms_profile)
        response = service.dispatch("search")
        self._assert_menu_response(
            response,
            expected_menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )

    def test_menu_search_additional_domain(self):
        self.menu1.sudo().move_line_search_additional_domain = [
            ("picking_id.priority", "=", "1")
        ]

        expected_counters = {
            self.menu1.id: {
                "lines_count": 0,
                "picking_count": 0,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
            self.menu2.id: {
                "lines_count": 6,
                "picking_count": 3,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
        }
        expected_menu_items = (
            self.env["shopfloor.menu"]
            .sudo()
            .search([("profile_id", "=", self.wms_profile.id)])
        )
        # ensures expected counters are in the expected menu items
        self.assertIn(self.menu1, expected_menu_items)
        self.assertIn(self.menu2, expected_menu_items)
        service = self.get_service("menu", profile=self.wms_profile)
        response = service.dispatch("search")
        self._assert_menu_response(
            response,
            expected_menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )

        self.menu1.sudo().move_line_search_additional_domain = [
            ("picking_id.priority", "=", "0")
        ]
        expected_counters = {
            self.menu1.id: {
                "lines_count": 2,
                "picking_count": 2,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
            self.menu2.id: {
                "lines_count": 6,
                "picking_count": 3,
                "priority_lines_count": 0,
                "priority_picking_count": 0,
            },
        }
        response = service.dispatch("search")
        self._assert_menu_response(
            response,
            expected_menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )

    def test_menu_search_counters_disabled_has_work(self):
        """When show_counters is False, counters are omitted and has_work is provided."""
        self.shopfloor_app.sudo().show_counters = False

        # Configure menu1 to have zero matching lines
        self.menu1.sudo().move_line_search_additional_domain = [("id", "=", 0)]

        service = self.get_service("menu", profile=self.wms_profile)
        response = service.dispatch("search")

        menu_items_by_id = {item["id"]: item for item in response["data"]["records"]}

        self.assertIn(self.menu1.id, menu_items_by_id)
        self.assertIn(self.menu2.id, menu_items_by_id)

        # menu1 has no lines matching domain -> has_work is False
        menu1_data = menu_items_by_id[self.menu1.id]
        self.assertFalse(menu1_data.get("has_work"))
        self.assertNotIn("lines_count", menu1_data)

        # menu2 has pending lines -> has_work is True
        menu2_data = menu_items_by_id[self.menu2.id]
        self.assertTrue(menu2_data.get("has_work"))
        self.assertNotIn("lines_count", menu2_data)
