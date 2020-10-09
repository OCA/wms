# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class LocationContentTransferSorter(Component):

    _name = "shopfloor.location.content.transfer.sorter"
    _inherit = "shopfloor.process.action"
    _usage = "location_content_transfer.sorter"

    def __init__(self, work_context):
        super().__init__(work_context)
        self._pickings = self.env["stock.picking"].browse()
        self._content = None

    def feed_pickings(self, pickings):
        self._pickings |= pickings

    def move_lines(self):
        """Returns valid move lines.

        Valid move lines are:
            - those not bound to a package level
            - those bound to invalid package levels

        An invalid package level has one of its line not targetting the
        expected package.
        """
        # lines without package level only (raw products)
        move_lines = self._pickings.move_line_ids.filtered(
            lambda line: not line.package_level_id
            and line.state not in ("cancel", "done")
        )
        # lines with invalid package levels
        invalid_levels = self._pickings.package_level_ids.filtered(
            lambda level: level.state not in ("cancel", "done")
            and any(
                line.result_package_id != level.package_id
                for line in level.move_line_ids
            )
        )
        return move_lines | invalid_levels.move_line_ids

    def package_levels(self):
        """Returns valid package levels.

        A valid package level has all its related move lines targetting
        the expected package.
        """
        return self._pickings.package_level_ids.filtered(
            lambda level: level.state not in ("cancel", "done")
            and all(
                line.result_package_id == level.package_id
                for line in level.move_line_ids
            )
        )

    @staticmethod
    def _sort_key(content):
        # content can be either a move line, either a package
        # level
        return (
            # postponed content after other contents
            content.shopfloor_priority or 10,
            # sort by shopfloor picking sequence
            content.location_dest_id.shopfloor_picking_sequence or "",
            # sort by similar destination
            content.location_dest_id.complete_name,
            # lines before packages (if we have raw products and packages, raw
            # will be on top? wild guess)
            0 if content._name == "stock.move.line" else 1,
            # to have a deterministic sort
            content.id,
        )

    def sort(self):
        content = [line for line in self.move_lines() if line] + [
            level for level in self.package_levels() if level
        ]
        self._content = sorted(content, key=self._sort_key)

    def __iter__(self):
        if self._content is None:
            self.sort()
        return iter(self._content)

    def __next__(self):
        return next(iter(self))
