# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from collections import defaultdict

from odoo.tools.float_utils import float_round

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    def _select_value_to_label(self, rec, fname):
        return rec._fields[fname].convert_to_export(rec[fname], rec)

    def location_detail(self, record, **kw):
        return self._jsonify(
            record.with_context(location=record.id), self._location_detail_parser, **kw
        )

    def locations_detail(self, record, **kw):
        return self.location_detail(record, multi=True)

    @property
    def _location_detail_parser(self):
        return self._location_parser + [
            "complete_name",
            (
                "quant_ids:products",
                lambda record, fname: self._location_content(record),
            ),
            (
                "reserved_move_line_ids:reserved_move_lines",
                lambda record, fname: self.move_lines(record[fname]),
            ),
        ]

    def _location_content(self, record):
        res = []
        product_qties = defaultdict(lambda: defaultdict(lambda: 0))
        for quant in record.quant_ids:
            product_qties[quant.product_id][quant.lot_id] += quant.quantity
        for product, quants_qty in product_qties.items():
            val = self.product(product)
            lots = []
            val["lots"] = lots
            qty_total = 0
            for lot, qty in quants_qty.items():
                qty_total += qty
                if not lot:
                    continue
                lot_val = self._location_lot(lot)
                lot_val["quantity"] = qty
                lots.append(lot_val)
            val["quantity"] = qty_total
            res.append(val)
        return res

    def _location_lot(self, record, **kw):
        # Define a new method to not overload the base one which is used in many places
        return self._jsonify(record, self._location_lot_detail_parser, **kw)

    @property
    def _location_lot_detail_parser(self):
        return self._lot_parser + [
            "removal_date",
        ]

    @ensure_model("stock.picking")
    def picking_detail(self, record, **kw):
        parser = self._picking_detail_parser
        # progress is a heavy computed field,
        # and it may reduce performance significatively
        # when dealing with a large number of pickings.
        # Thus, we make it optional.
        if "with_progress" in kw:
            parser.append("progress")
        return self._jsonify(record, parser, **kw)

    def pickings_detail(self, record, **kw):
        return self.picking_detail(record, multi=True)

    @property
    def _picking_detail_parser(self):
        return self._picking_parser + [
            "picking_type_code",
            ("priority", self._select_value_to_label),
            "scheduled_date",
            ("picking_type_id:operation_type", ["id", "name"]),
            (
                "move_line_ids:move_lines",
                lambda record, fname: self.move_lines(record[fname]),
            ),
        ]

    def package_detail(self, record, picking=None, **kw):
        # Define a new method to not overload the base one which is used in many places
        data = self.package(record, picking=picking, with_packaging=True, **kw)
        data.update(self._jsonify(record, self._package_detail_parser, **kw))
        return data

    def packages_detail(self, records, picking=None, **kw):
        return [self.package_detail(rec, picking=picking) for rec in records]

    @property
    def _package_detail_parser(self):
        return [
            (
                "reserved_move_line_ids:pickings",
                lambda record, fname: self.pickings(record[fname].mapped("picking_id")),
            ),
            (
                "reserved_move_line_ids:move_lines",
                lambda record, fname: self.move_lines(record[fname]),
            ),
            ("location_id:location", ["id", "display_name:name"]),
        ]

    @ensure_model("stock.lot")
    def lot_detail(self, record, **kw):
        # Define a new method to not overload the base one which is used in many places
        return self._jsonify(record, self._lot_detail_parser, **kw)

    def lots_detail(self, record, **kw):
        return self.lot_detail(record, multi=True)

    @property
    def _lot_detail_parser(self):
        return self._lot_parser + [
            "removal_date",
            (
                "product_id:product",
                lambda record, fname: self.product_detail(record[fname]),
            ),
        ]

    @ensure_model("product.product")
    def product_detail(self, record, **kw):
        # Defined new method to not overload the base one used in many places
        data = self._jsonify(record, self._product_detail_parser, **kw)
        suppliers = self.env["product.supplierinfo"].search(
            [("product_id", "=", record.id)]
        )
        data["suppliers"] = self._jsonify(
            suppliers, self._product_supplierinfo_parser, multi=True
        )
        return data

    def products_detail(self, record, **kw):
        return self.product_detail(record, multi=True)

    @property
    def _product_parser(self):
        return super()._product_parser + [
            "qty_available",
            ("free_qty:qty_reserved", self._product_reserved_qty_subparser),
        ]

    def _product_reserved_qty_subparser(self, rec, field_name):
        # free_qty = qty_available - reserved_quantity
        return float_round(
            rec.qty_available - rec[field_name], precision_rounding=rec.uom_id.rounding
        )

    @property
    def _product_detail_parser(self):
        return self._product_parser + [
            ("image_128:image", self._product_image_url),
            (
                "stock_quant_ids:locations",
                lambda record, fname: self._locations_for_product(record),
            ),
            (
                "product_tmpl_id:manufacturer",
                lambda rec, fname: self._jsonify(
                    rec.product_tmpl_id.manufacturer_id, ["id", "name"]
                ),
            ),
        ]

    def _get_product_locations(self, record):
        # Retrieve all products -- maybe more than one location
        product_template = record.product_tmpl_id
        products = product_template.product_variant_ids
        quants = self.env["stock.quant"].search(
            [("product_id", "in", products.ids), ("location_id.usage", "=", "internal")]
        )
        return quants.location_id

    def _locations_for_product(self, record):
        res = []
        for location in self._get_product_locations(record):
            quants = location.quant_ids.filtered(lambda q: q.product_id == record)
            loc = self.location(location)
            loc["complete_name"] = location.complete_name
            loc["quantity"] = sum(quants.mapped("quantity"))
            lots = []
            quants_lot_qty = defaultdict(lambda: 0)
            for quant in quants:
                quants_lot_qty[quant.lot_id] += quant.quantity
            for lot, qty in quants_lot_qty.items():
                if not lot:
                    continue
                lot_val = self._location_lot(lot)
                lot_val["quantity"] = qty
                lots.append(lot_val)
            loc["lots"] = lots
            res.append(loc)
        return res

    def _product_image_url(self, record, field_name):
        if not record[field_name]:
            return None
        return f"/web/image/product.product/{record.id}/{field_name}"

    @property
    def _product_supplierinfo_parser(self):
        return [
            ("id", lambda rec, fname: rec.partner_id.id),
            ("partner_id:partner", lambda rec, fname: rec.partner_id.name),
            "product_name",
            "product_code",
        ]

    @ensure_model("product.packaging")
    def packaging_detail(self, record, **kw):
        return self._jsonify(
            record.with_context(packaging=record.id),
            self._packaging_detail_parser,
            **kw,
        )

    @property
    def _packaging_detail_parser(self):
        return self._packaging_parser + [
            "packaging_length:length",
            "width",
            "height",
            ("max_weight", lambda rec, fname: rec.package_type_id.max_weight),
            "length_uom_name:length_uom",
            "weight_uom_name:weight_uom",
            "barcode:barcode",
        ]
