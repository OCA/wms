from odoo.addons.component.core import Component


class DataAction(Component):
    """Provide methods to share data structures

    The methods should be used in Service Components, so we try to
    have similar data structures across scenarios.
    """

    _name = "shopfloor.data.action"
    _inherit = "shopfloor.process.action"
    _usage = "data"

    def _jsonify(self, recordset, parser, multi=False, **kw):
        res = recordset.jsonify(parser)
        if not multi:
            return res[0] if res else None
        return res

    def partner(self, record, **kw):
        return self._jsonify(record, self._partner_parser, **kw)

    def partners(self, record, **kw):
        return self.partner(record, multi=True)

    @property
    def _partner_parser(self):
        return ["id", "name"]

    def picking(self, record, **kw):
        return self._jsonify(record, self._picking_parser, **kw)

    def pickings(self, record, **kw):
        return self.picking(record, multi=True)

    @property
    def _picking_parser(self):
        return [
            "id",
            "name",
            "origin",
            "note",
            ("partner_id:partner", self._partner_parser),
            "move_line_count",
            "total_weight:weight",
        ]

    def package(self, record, picking=None, **kw):
        """Return data for a stock.quant.package

        If a picking is given, it will include the number of lines of the package
        for the picking.
        """
        data = self._jsonify(record, self._package_parser, **kw)
        # handle special cases
        if data and picking:
            # TODO: exclude canceled and done?
            lines = picking.move_line_ids.filtered(lambda l: l.package_id == record)
            data.update({"move_line_count": len(lines)})
        return data

    def packages(self, records, picking=None, **kw):
        return [self.package(rec, picking=picking) for rec in records]

    @property
    def _package_parser(self):
        return [
            "id",
            "name",
            "pack_weight:weight",
            ("product_packaging_id:packaging", self._packaging_parser),
        ]

    def packaging(self, record, **kw):
        return self._jsonify(record, self._packaging_parser, **kw)

    def packagings(self, record, **kw):
        return self.packaging(record, multi=True)

    @property
    def _packaging_parser(self):
        return ["id", "name"]

    def lot(self, record, **kw):
        return self._jsonify(record, self._lot_parser, **kw)

    def lots(self, record, **kw):
        return self.lot(record, multi=True)

    @property
    def _lot_parser(self):
        return ["id", "name", "ref"]

    def location(self, record, **kw):
        return self._jsonify(record, self._location_parser, **kw)

    def locations(self, record, **kw):
        return self.location(record, multi=True)

    @property
    def _location_parser(self):
        return ["id", "name"]

    def move_line(self, record, **kw):
        data = self._jsonify(record, self._move_line_parser)
        if data:
            data.update(
                {
                    "package_src": self.package(record.package_id, record.picking_id),
                    "package_dest": self.package(
                        record.result_package_id, record.picking_id,
                    ),
                }
            )
        return data

    def move_lines(self, records, **kw):
        return [self.move_line(rec) for rec in records]

    @property
    def _move_line_parser(self):
        return [
            "id",
            "qty_done",
            "product_uom_qty:quantity",
            ("product_id:product", self._product_parser),
            ("lot_id:lot", self._lot_parser),
            ("location_id:location_src", self._location_parser),
            ("location_dest_id:location_dest", self._location_parser),
        ]

    def product(self, record, **kw):
        return self._jsonify(record, self._product_parser, **kw)

    def products(self, record, **kw):
        return self.product(record, multi=True)

    @property
    def _product_parser(self):
        return ["id", "name", "display_name", "default_code"]

    def picking_batch(self, record, with_pickings=True, **kw):
        parser = self._picking_batch_parser
        if with_pickings:
            parser.append(("picking_ids:pickings", self._picking_parser))
        return self._jsonify(record, parser, **kw)

    def picking_batches(self, record, **kw):
        return self.picking_batch(record, multi=True)

    @property
    def _picking_batch_parser(self):
        return ["id", "name", "picking_count", "move_line_count", "total_weight:weight"]
