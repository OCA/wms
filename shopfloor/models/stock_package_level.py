# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StockPackageLevel(models.Model):
    _name = "stock.package_level"
    _inherit = ["stock.package_level", "shopfloor.priority.postpone.mixin"]

    # we search package levels based on their package in some workflows
    package_id = fields.Many2one(index=True)
    # allow domain on picking_id.xxx without too much perf penalty
    picking_id = fields.Many2one(auto_join=True)

    def explode_package(self):
        """Unlink but keep the moves.

        Original motivation:

        A package level has a relation to "move_ids" only when the
        package level was created first from the UI and it created
        its move.
        When we unlink a package level, it deletes the move it created.
        But in some cases, we want to keep the move, e.g.:

        * create a package level from the UI to move a package
        * it generates a move for the matching product quantity
        * we use a barcode scenario such as cluster or zone picking
        * we use the "replace package" button
        * when replacing the package, we have to delete the package level,
          but we still have the same need in term of "I want X products",
          so we have to keep the move
        * another case is when we "dismiss" the package level in the location
          content transfer scenario, we want to keep the "need" in moves, but
          we are no longer moving the entire package level

        Commit

        https://github.com/odoo/odoo/commit/b33e72d0bf027fb2c789b1b9476f7edf1a40b0a6

        introduced the handling of pkg level deletion
        which is doing what was done by this method.

        Moreover it has been fixed here https://github.com/odoo/odoo/pull/66517.

        Hence, we keep this method to unify the action of "exploding a package"
        especially to avoid to refactor many places every time the core changes.
        """
        # This will trigger the deletion of the pkg level
        self.move_line_ids.result_package_id = False
