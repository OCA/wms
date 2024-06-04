# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools.float_utils import float_round

from odoo.addons.shopfloor_base.tests.common_misc import ActionsDataTestMixin

from .common import CommonCase


# pylint: disable=missing-return
class ActionsDataCaseBase(CommonCase, ActionsDataTestMixin):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packaging_type = (
            cls.env["product.packaging.level"]
            .sudo()
            .create({"name": "Transport Box", "code": "TB", "sequence": 0})
        )
        cls.packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create({"name": "Pallet", "packaging_level_id": cls.packaging_type.id})
        )
        cls.delivery_packaging = (
            cls.env["stock.package.type"]
            .sudo()
            .create(
                {
                    "name": "Pallet",
                    "package_carrier_type": "none",
                    "barcode": "PALCODE",
                }
            )
        )
        cls.product_b.tracking = "lot"
        cls.product_c.tracking = "lot"
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.picking.scheduled_date = "2020-08-03"
        # put product A in a package
        cls.move_a = cls.picking.move_ids[0]
        cls._fill_stock_for_moves(cls.move_a, in_package=True)
        # product B has a lot
        cls.move_b = cls.picking.move_ids[1]
        cls._fill_stock_for_moves(cls.move_b, in_lot=True)
        # product C has a lot and package
        cls.move_c = cls.picking.move_ids[2]
        cls._fill_stock_for_moves(cls.move_c, in_package=True, in_lot=True)
        # product D is raw
        cls.move_d = cls.picking.move_ids[3]
        cls._fill_stock_for_moves(cls.move_d)
        (cls.move_a + cls.move_b + cls.move_c + cls.move_d).write({"priority": "1"})
        cls.picking.action_assign()

        cls.supplier = cls.env["res.partner"].sudo().create({"name": "Supplier"})
        cls.product_a_vendor = (
            cls.env["product.supplierinfo"]
            .sudo()
            .create(
                {
                    "partner_id": cls.supplier.id,
                    "price": 8.0,
                    "product_code": "VENDOR_CODE_A",
                    "product_id": cls.product_a.id,
                    "product_tmpl_id": cls.product_a.product_tmpl_id.id,
                }
            )
        )
        cls.product_a_variant = cls.product_a.copy(
            {
                "name": "Product A variant 1",
                "type": "product",
                "default_code": "A-VARIANT",
                "barcode": "A-VARIANT",
            }
        )
        # create another supplier info w/ lower sequence
        cls.product_a_vendor = (
            cls.env["product.supplierinfo"]
            .sudo()
            .create(
                {
                    "partner_id": cls.supplier.id,
                    "price": 12.0,
                    "product_code": "VENDOR_CODE_VARIANT",
                    "product_id": cls.product_a_variant.id,
                    "product_tmpl_id": cls.product_a.product_tmpl_id.id,
                    "sequence": 0,
                }
            )
        )
        cls.product_a_variant.flush_recordset()
        cls.product_a_vendor.flush_recordset()

    def _expected_location(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "barcode": record.barcode,
        }
        data.update(kw)
        return data

    def _expected_product(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "display_name": record.display_name,
            "default_code": record.default_code,
            "barcode": record.barcode,
            "packaging": [
                self._expected_packaging(x) for x in record.packaging_ids if x.qty
            ],
            "uom": {
                "factor": record.uom_id.factor,
                "id": record.uom_id.id,
                "name": record.uom_id.name,
                "rounding": record.uom_id.rounding,
            },
            "supplier_code": self._expected_supplier_code(record),
        }
        data.update(kw)
        return data

    def _expected_supplier_code(self, product):
        supplier_info = product.seller_ids.filtered(lambda x: x.product_id == product)
        return supplier_info[0].product_code if supplier_info else ""

    def _expected_packaging(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.packaging_level_id.name,
            "code": record.packaging_level_id.code,
            "qty": record.qty,
        }
        data.update(kw)
        return data

    def _expected_delivery_packaging(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "packaging_type": record.package_carrier_type,
            "barcode": record.barcode,
        }
        data.update(kw)
        return data

    def _expected_storage_type(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
        }
        data.update(kw)
        return data

    def _expected_package(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "weight": record.pack_weight or record.estimated_pack_weight_kg,
            "storage_type": None,
            "total_quantity": sum(record.quant_ids.mapped("quantity")),
        }
        data.update(kw)
        return data


class ActionsDataDetailCaseBase(ActionsDataCaseBase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.lot = cls.env["stock.lot"].create(
            {"product_id": cls.product_b.id, "company_id": cls.env.company.id}
        )
        cls.package = cls.move_a.move_line_ids.package_id

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )

    def _expected_location_detail(self, record, **kw):
        return dict(
            **self._expected_location(record),
            **{
                "complete_name": record.complete_name,
                "reserved_move_lines": self.data_detail.move_lines(
                    kw.get("move_lines", [])
                ),
            }
        )

    def _expected_product_detail(self, record, **kw):
        qty_available = record.qty_available
        qty_reserved = float_round(
            record.qty_available - record.free_qty,
            precision_rounding=record.uom_id.rounding,
        )
        detail = {
            "qty_available": qty_available,
            "qty_reserved": qty_reserved,
        }
        if kw.get("full"):
            detail.update(
                {
                    "image": "/web/image/product.product/{}/image_128".format(record.id)
                    if record.image_128
                    else None,
                    "manufacturer": {
                        "id": record.manufacturer_id.id,
                        "name": record.manufacturer_id.name,
                    }
                    if record.manufacturer_id
                    else None,
                    "suppliers": [
                        {
                            "id": v.partner_id.id,
                            "partner": v.partner_id.name,
                            "product_name": None,
                            "product_code": v.product_code,
                        }
                        for v in record.seller_ids
                    ],
                }
            )
        return dict(**self._expected_product(record), **detail)

    def _expected_packaging_detail(self, record, **kw):
        return dict(
            **self._expected_packaging(record),
            **{
                "length": record.packaging_length,
                "width": record.width,
                "height": record.height,
                "max_weight": record.package_type_id.max_weight,
                "length_uom": record.length_uom_name,
                "weight_uom": record.weight_uom_name,
                "barcode": record.barcode,
            }
        )
