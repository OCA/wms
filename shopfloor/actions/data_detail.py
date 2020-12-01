# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools.float_utils import float_round

from odoo.addons.component.core import Component


class DataDetailAction(Component):
    """Provide extra data on top of data action.
    """

    _name = "shopfloor.data.detail.action"
    _inherit = "shopfloor.data.action"
    _usage = "data_detail"

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
                "reserved_move_line_ids:reserved_move_lines",
                lambda record, fname: self.move_lines(record[fname]),
            ),
        ]

    def picking_detail(self, record, **kw):
        return self._jsonify(record, self._picking_detail_parser, **kw)

    def pickings_detail(self, record, **kw):
        return self.picking_detail(record, multi=True)

    @property
    def _picking_detail_parser(self):
        return self._picking_parser + [
            "picking_type_code",
            ("priority", self._select_value_to_label),
            "scheduled_date",
            ("picking_type_id:operation_type", ["id", "name"]),
            ("carrier_id:carrier", ["id", "name"]),
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
        ]

    def lot_detail(self, record, **kw):
        # Define a new method to not overload the base one which is used in many places
        return self._jsonify(record, self._lot_detail_parser, **kw)

    def lots_detail(self, record, **kw):
        return self.lot_detail(record, multi=True)

    @property
    def _lot_detail_parser(self):
        return self._lot_parser + [
            "removal_date",
            "life_date:expire_date",
            (
                "product_id:product",
                lambda record, fname: self.product_detail(record[fname]),
            ),
        ]

    def product_detail(self, record, **kw):
        # Defined new method to not overload the base one used in many places
        data = self._jsonify(record, self._product_detail_parser, **kw)
        suppliers = self.env["product.supplierinfo"].search(
            [("product_id", "=", record.id)]
        )
        data["suppliers"] = suppliers.jsonify(self._product_supplierinfo_parser)
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
                "product_tmpl_id:manufacturer",
                lambda rec, fname: self._jsonify(
                    rec.product_tmpl_id.manufacturer, ["id", "name"]
                ),
            ),
        ]

    def _product_image_url(self, record, field_name):
        if not record[field_name]:
            return None
        return "/web/image/product.product/{}/{}".format(record.id, field_name)

    @property
    def _product_supplierinfo_parser(self):
        return [
            # supplier.name == partner :/
            ("id", lambda rec, fname: rec.name.id),
            ("name", lambda rec, fname: rec.name.name),
            "product_name",
            "product_code",
        ]
