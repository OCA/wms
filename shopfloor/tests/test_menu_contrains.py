# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import exceptions

from .test_menu_base import MenuCountersCommonCase


class TestMenuContrains(MenuCountersCommonCase):
    def test_move_line_search_sort_order_custom_code_invalid(self):

        with self.assertRaises(exceptions.ValidationError):
            # wrong indentation in python code
            self.menu1.sudo().write(
                {
                    "move_line_search_sort_order_custom_code": """
  key = 1
  toto(1)
""",
                    "move_line_search_sort_order": "custom_code",
                }
            )

        self.menu1.sudo().write(
            {
                "move_line_search_sort_order_custom_code": "key = 1",
                "move_line_search_sort_order": "custom_code",
            }
        )

    def test_move_line_search_sort_order_mismatch(self):
        with self.assertRaises(exceptions.ValidationError):
            self.menu1.sudo().move_line_search_sort_order = "custom_code"

        self.menu1.sudo().write(
            {
                "move_line_search_sort_order_custom_code": "key = 1",
                "move_line_search_sort_order": "priority",
            }
        )
        self.assertFalse(self.menu1.move_line_search_sort_order_custom_code)
