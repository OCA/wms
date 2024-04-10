# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("stock.location")
    def location(self, record, **kw):
        parser = self._location_parser
        data = self._jsonify(record.with_context(location=record.id), parser, **kw)
        if kw.get("with_operation_progress"):
            lines_blacklist = (
                kw.get("progress_lines_blacklist")
                or self.env["stock.move.line"].browse()
            )
            domain = [
                ("location_id", "=", record.id),
                ("state", "in", ["partially_available", "assigned"]),
                ("picking_id.state", "=", "assigned"),
                ("id", "not in", lines_blacklist.ids),
            ]
            operation_progress = self._get_operation_progress(domain)
            data.update({"operation_progress": operation_progress})
        return data

    def locations(self, records, **kw):
        return [self.location(rec, **kw) for rec in records]

    @property
    def _location_parser(self):
        return [
            "id",
            "name",
            # Fallback to name if barcode is not valued.
            ("barcode", lambda rec, fname: rec[fname] if rec[fname] else rec.name),
        ]

    def _get_picking_parser(self, record, **kw):
        parser = self._picking_parser
        # progress is a heavy computed field,
        # and it may reduce performance significatively
        # when dealing with a large number of pickings.
        # Thus, we make it optional.
        if kw.get("with_progress"):
            parser.append("progress")
        return parser

    @ensure_model("stock.picking")
    def picking(self, record, **kw):
        return self._jsonify(record, self._get_picking_parser(record, **kw), **kw)

    def pickings(self, record, **kw):
        return self.picking(record, multi=True)

    @property
    def _picking_parser(self, **kw):
        return [
            "id",
            "name",
            "origin",
            "note",
            ("partner_id:partner", self._partner_parser),
            ("carrier_id:carrier", self._simple_record_parser()),
            ("ship_carrier_id:ship_carrier", self._simple_record_parser()),
            "move_line_count",
            "package_level_count",
            "bulk_line_count",
            "total_weight:weight",
            "scheduled_date",
            "priority",
        ]

    @ensure_model("stock.quant.package")
    def package(self, record, picking=None, with_packaging=False, **kw):
        """Return data for a stock.quant.package

        If a picking is given, it will include the number of lines of the package
        for the picking.
        """
        parser = self._package_parser
        if with_packaging:
            parser += self._package_packaging_parser
        data = self._jsonify(record, parser, **kw)
        qty = len(record.quant_ids)
        # handle special cases
        progress_package_key = ""
        if kw.get("with_operation_progress_src"):
            progress_package_key = "package_id"
        elif kw.get("with_operation_progress_dest"):
            progress_package_key = "result_package_id"
        if progress_package_key:
            lines_blacklist = (
                kw.get("progress_lines_blacklist")
                or self.env["stock.move.line"].browse()
            )
            domain = [
                (progress_package_key, "=", record.id),
                ("state", "in", ["partially_available", "assigned"]),
                ("picking_id.state", "=", "assigned"),
                ("id", "not in", lines_blacklist.ids),
            ]
            operation_progress = self._get_operation_progress(domain)
            data.update({"operation_progress": operation_progress})
        if kw.get("with_package_move_line_count") and data and picking:
            move_line_count = self.env["stock.move.line"].search_count(
                [
                    ("picking_id.picking_type_id", "=", picking.picking_type_id.id),
                    ("result_package_id", "=", record.id),
                    ("state", "in", ["partially_available", "assigned"]),
                ]
            )
            qty += move_line_count
            # TODO does this name really makes sense?
            data.update({"move_line_count": qty})
        return data

    def packages(self, records, picking=None, **kw):
        return [self.package(rec, picking=picking, **kw) for rec in records]

    @property
    def _package_parser(self):
        return [
            "id",
            "name",
            "shopfloor_weight:weight",
            ("package_storage_type_id:storage_type", ["id", "name"]),
            (
                "quant_ids:total_quantity",
                lambda rec, fname: sum(rec.quant_ids.mapped("quantity")),
            ),
        ]

    @property
    def _package_packaging_parser(self):
        return [
            ("packaging_id:packaging", self._packaging_parser),
        ]

    @ensure_model("product.packaging")
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
            ("packaging_type_id:shopfloor_icon", self._packaging_icon_data),
            "qty",
        ]

    @ensure_model("product.packaging")
    def delivery_packaging(self, record, **kw):
        return self._jsonify(record, self._delivery_packaging_parser, **kw)

    def delivery_packaging_list(self, records, **kw):
        return self.delivery_packaging(records, multi=True)

    @property
    def _delivery_packaging_parser(self):
        return [
            "id",
            "name",
            (
                "packaging_type_id:packaging_type",
                lambda rec, fname: rec.packaging_type_id.display_name,
            ),
            "barcode",
        ]

    @ensure_model("stock.production.lot")
    def lot(self, record, **kw):
        return self._jsonify(record, self._lot_parser, **kw)

    def lots(self, record, **kw):
        return self.lot(record, multi=True)

    @property
    def _lot_parser(self):
        return self._simple_record_parser() + ["ref", "expiration_date"]

    @ensure_model("stock.move.line")
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
                        record.result_package_id.with_context(
                            picking_id=record.picking_id.id
                        ),
                        record.picking_id,
                        **kw,
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
            (
                "move_id:priority",
                lambda rec, fname: rec.move_id.priority or "",
            ),
            "progress",
        ]

    @ensure_model("stock.move")
    def move(self, record, **kw):
        record = record.with_context(location=record.location_id.id)
        parser = self._move_parser
        return self._jsonify(record, parser)

    def moves(self, records, **kw):
        return [self.move(rec, **kw) for rec in records]

    @property
    def _move_parser(self):
        return [
            "id",
            "quantity_done",
            "product_uom_qty:quantity",
            ("product_id:product", self._product_parser),
            ("location_id:location_src", self._location_parser),
            ("location_dest_id:location_dest", self._location_parser),
            "priority",
            "progress",
        ]

    @ensure_model("stock.package_level")
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
            # TODO: allow to pass mapped path to jsonifier
            (
                "package_id:quantity",
                lambda rec, fname: rec.package_id.single_product_qty,
            ),
        ]

    @ensure_model("product.product")
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

    def _packaging_icon_data(self, rec, field):
        icon_data = {"alt_text": rec.packaging_type_id.name}
        if not rec.packaging_type_id.shopfloor_icon:
            return icon_data
        icon_data[
            "url"
        ] = "/web/image/product.packaging.type/{}/shopfloor_icon/30x30".format(
            rec.packaging_type_id.id
        )
        return icon_data

    def _product_supplier_code(self, rec, field):
        supplier_info = fields.first(
            rec.seller_ids.filtered(lambda x: x.product_id == rec)
        )
        return supplier_info.product_code or ""

    @ensure_model("stock.picking.batch")
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

    @ensure_model("stock.picking.type")
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

    def _get_operation_progress(self, domain):
        lines = self.env["stock.move.line"].search(domain)
        # operations_to_do = number of total operations that are pending for this location.
        # operations_done = number of operations already done.
        # A line with an assigned package counts as 1 operation.
        operations_to_do = 0
        operations_done = 0
        for line in lines:
            is_done = line.qty_done == line.product_uom_qty
            package_qty_done = 1 if is_done else 0
            operations_done += (
                line.qty_done if not line.package_id else package_qty_done
            )
            operations_to_do += line.product_uom_qty if not line.package_id else 1
        return {
            "done": operations_done,
            "to_do": operations_to_do,
        }
