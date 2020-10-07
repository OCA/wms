from odoo import models


class StockPackageLevel(models.Model):
    _name = "stock.package_level"
    _inherit = ["stock.package_level", "shopfloor.priority.postpone.mixin"]

    def replace_package(self, new_package):
        """Replace a package on an assigned package level and related records

        The replacement package must have the same properties (same products
        and quantities).
        """
        if self.state not in ("new", "assigned"):
            return

        move_lines = self.move_line_ids
        # the write method on stock.move.line updates the reservation on quants
        move_lines.package_id = new_package
        # when a package is set on a line, the destination package is the same
        # by default
        move_lines.result_package_id = new_package
        for quant in new_package.quant_ids:
            for line in move_lines:
                if line.product_id == quant.product_id:
                    line.lot_id = quant.lot_id
                    line.owner_id = quant.owner_id

        self.package_id = new_package

    def shallow_unlink(self):
        """Unlink but keep the moves
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
        """
        self.move_ids.package_level_id = False
        self.unlink()

    def explode_package(self):
        move_lines = self.move_line_ids
        move_lines.result_package_id = False
        self.shallow_unlink()
