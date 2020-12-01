# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_menu_base import MenuCountersCommonCase


class TestMenuCountersCommonCase(MenuCountersCommonCase):
    def test_menu_search(self):
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
        response = self.service.dispatch("search")
        self._assert_menu_response(
            response,
            self.menu_items.sorted("sequence"),
            expected_counters=expected_counters,
        )
