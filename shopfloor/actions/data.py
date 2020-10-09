# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields

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

    def _simple_record_parser(self):
        return ["id", "name"]

    def partner(self, record, **kw):
        return self._jsonify(record, self._partner_parser, **kw)

    def partners(self, record, **kw):
        return self.partner(record, multi=True)

    @property
    def _partner_parser(self):
        return self._simple_record_parser()

    def location(self, record, **kw):
        return self._jsonify(
            record.with_context(location=record.id), self._location_parser, **kw
        )

    def locations(self, record, **kw):
        return self.location(record, multi=True)

    @property
    def _location_parser(self):
        return ["id", "name", "barcode"]

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
            "scheduled_date",
        ]

    def package(self, record, picking=None, with_packaging=False, **kw):
        """Return data for a stock.quant.package

        If a picking is given, it will include the number of lines of the package
        for the picking.
        """
        parser = self._package_parser
        if with_packaging:
            parser += self._package_packaging_parser
        data = self._jsonify(record, parser, **kw)
        # handle special cases
        if data and picking:
            # TODO: exclude canceled and done?
            lines = picking.move_line_ids.filtered(lambda l: l.package_id == record)
            data.update({"move_line_count": len(lines)})
        return data

    def packages(self, records, picking=None, **kw):
        return [self.package(rec, picking=picking, **kw) for rec in records]

    @property
    def _package_parser(self):
        return [
            "id",
            "name",
            "pack_weight:weight",
            ("package_storage_type_id:storage_type", ["id", "name"]),
        ]

    @property
    def _package_packaging_parser(self):
        return [
            ("packaging_id:packaging", self._packaging_parser),
        ]

    def packaging(self, record, **kw):
        return self._jsonify(record, self._packaging_parser, **kw)

    def packaging_list(self, record, **kw):
        return self.packaging(record, multi=True)

    @property
    def _packaging_parser(self):
        return [
            "id",
            ("packaging_type_id:name", lambda rec, fname: rec.packaging_type_id.name),
            ("packaging_type_id:code", lambda rec, fname: rec.packaging_type_id.code),
            "qty",
        ]

    def lot(self, record, **kw):
        return self._jsonify(record, self._lot_parser, **kw)

    def lots(self, record, **kw):
        return self.lot(record, multi=True)

    @property
    def _lot_parser(self):
        return self._simple_record_parser() + ["ref"]

    def move_line(self, record, with_picking=False, **kw):
        record = record.with_context(location=record.location_id.id)
        parser = self._move_line_parser
        if with_picking:
            parser += [("picking_id:picking", self._picking_parser)]
        data = self._jsonify(record, parser)
        if data:
            data.update(
                {
                    # cannot use sub-parser here
                    # because result might depend on picking
                    "package_src": self.package(
                        record.package_id, record.picking_id, **kw
                    ),
                    "package_dest": self.package(
                        record.result_package_id, record.picking_id, **kw
                    ),
                }
            )
        return data

    def move_lines(self, records, **kw):
        return [self.move_line(rec, **kw) for rec in records]

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
            ("move_id:priority", lambda rec, fname: rec.move_id.priority or "",),
        ]

    def package_level(self, record, **kw):
        return self._jsonify(record, self._package_level_parser)

    def package_levels(self, records, **kw):
        return [self.package_level(rec, **kw) for rec in records]

    @property
    def _package_level_parser(self):
        return [
            "id",
            "is_done",
            ("picking_id:picking", self._simple_record_parser()),
            ("package_id:package_src", self._package_parser),
            ("location_dest_id:location_dest", self._location_parser),
            (
                "location_id:location_src",
                lambda rec, fname: self.location(
                    fields.first(rec.move_line_ids).location_id
                    or fields.first(rec.move_ids).location_id
                    or rec.picking_id.location_id
                ),
            ),
            # tnx to stock_quant_package_product_packaging
            (
                "package_id:product",
                lambda rec, fname: self.product(rec.package_id.single_product_id),
            ),
            # TODO: allow to pass mapped path to base_jsonify
            (
                "package_id:quantity",
                lambda rec, fname: rec.package_id.single_product_qty,
            ),
        ]

    def product(self, record, **kw):
        return self._jsonify(record, self._product_parser, **kw)

    def products(self, record, **kw):
        return self.product(record, multi=True)

    @property
    def _product_parser(self):
        return [
            "id",
            "name",
            "display_name",
            "default_code",
            "barcode",
            ("packaging_ids:packaging", self._product_packaging),
            ("uom_id:uom", self._simple_record_parser() + ["factor", "rounding"]),
            ("seller_ids:supplier_code", self._product_supplier_code),
        ]

    def _product_packaging(self, rec, field):
        return self._jsonify(
            rec.packaging_ids.filtered(lambda x: x.qty),
            self._packaging_parser,
            multi=True,
        )

    def _product_supplier_code(self, rec, field):
        supplier_info = fields.first(
            rec.seller_ids.filtered(lambda x: x.product_id == rec)
        )
        return supplier_info.product_code or ""

    def picking_batch(self, record, with_pickings=False, **kw):
        parser = self._picking_batch_parser
        if with_pickings:
            parser.append(("picking_ids:pickings", self._picking_parser))
        return self._jsonify(record, parser, **kw)

    def picking_batches(self, record, with_pickings=False, **kw):
        return self.picking_batch(record, with_pickings=with_pickings, multi=True)

    @property
    def _picking_batch_parser(self):
        return ["id", "name", "picking_count", "move_line_count", "total_weight:weight"]

    def picking_type(self, record, **kw):
        parser = self._picking_type_parser
        return self._jsonify(record, parser, **kw)

    def picking_types(self, record, **kw):
        return self.picking_type(record, multi=True)

    @property
    def _picking_type_parser(self):
        return [
            "id",
            "name",
        ]
