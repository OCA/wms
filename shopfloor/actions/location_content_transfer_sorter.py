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
        return self._pickings.move_line_ids.filtered(
            # lines without package level only (raw products)
            lambda line: not line.package_level_id
            and line.state not in ("cancel", "done")
        )

    def package_levels(self):
        return self._pickings.package_level_ids.filtered(
            lambda level: level.state not in ("cancel", "done")
        )

    @staticmethod
    def _sort_key(content):
        # content can be either a move line, either a package
        # level
        return (
            # postponed content after other contents
            int(content.shopfloor_postponed),
            # sort by shopfloor picking sequence
            content.location_dest_id.shopfloor_picking_sequence,
            # sort by similar destination
            content.location_dest_id.complete_name,
            # lines before packages (if we have raw products and packages, raw
            # will be on top? wild guess)
            0 if content._name == "stock.move.line" else 1,
            # to have a deterministic sort
            content.id,
        )

    def sort(self):
        content = [line for line in self.move_lines()] + [
            level for level in self.package_levels()
        ]
        self._content = sorted(content, key=self._sort_key)

    def __iter__(self):
        if self._content is None:
            self.sort()
        return iter(self._content)

    def __next__(self):
        return next(iter(self))
