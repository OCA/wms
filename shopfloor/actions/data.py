from odoo.addons.component.core import Component


class DataAction(Component):
    """Provide methods to share data structures

    The methods should be used in Service Components, so we try to
    have similar data structures across scenarios.
    """

    _name = "shopfloor.data.action"
    _inherit = "shopfloor.process.action"
    _usage = "data"

    def picking_summary(self, picking):
        return {
            "id": picking.id,
            "name": picking.name,
            "origin": picking.origin or "",
            "note": picking.note or "",
            "line_count": len(picking.move_line_ids),
            "partner": {"id": picking.partner_id.id, "name": picking.partner_id.name}
            if picking.partner_id
            else None,
        }

    def package(self, package, picking=None):
        """Return data for a stock.quant.package

        If a picking is given, it will include the number of lines of the package
        for the picking.
        """
        line_count = (
            len(picking.move_line_ids.filtered(lambda l: l.package_id == package))
            if picking
            else 0
        )
        return {
            "id": package.id,
            "name": package.name,
            # TODO
            "weight": 0,
            "line_count": line_count,
            "packaging_name": package.product_packaging_id.name or "",
        }

    def packaging(self, packaging):
        return {"id": packaging.id, "name": packaging.name}

    def lot(self, lot):
        return {"id": lot.id, "name": lot.name}

    def location(self, location):
        return {"id": location.id, "name": location.name}

    def move_line(self, move_line):
        return {
            "id": move_line.id,
            "qty_done": move_line.qty_done,
            "quantity": move_line.product_uom_qty,
            "product": {
                "id": move_line.product_id.id,
                "name": move_line.product_id.name,
                "display_name": move_line.product_id.display_name,
                "default_code": move_line.product_id.default_code or "",
            },
            "lot": {"id": move_line.lot_id.id, "name": move_line.lot_id.name}
            if move_line.lot_id
            else None,
            "package_src": self.package(move_line.package_id, move_line.picking_id)
            if move_line.package_id
            else None,
            "package_dest": self.package(
                move_line.result_package_id, move_line.picking_id
            )
            if move_line.result_package_id
            else None,
            "location_src": self.location(move_line.location_id),
            "location_dest": self.location(move_line.location_dest_id),
        }

    def _jsonify(self, recordset, parser):
        res = recordset.jsonify(parser)
        if len(recordset.ids) == 1:
            return res[0]
        return res

    def picking_batch(self, record):
        return self._jsonify(record, self._picking_batch_parser)

    @property
    def _picking_batch_parser(self):
        return ["id", "name", "picking_count", "move_line_count", "total_weight:weight"]
