from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorPack(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.pack"
    _usage = "pack"

    def scan(self, pack_name):
        """Scan a pack barcode"""
        pack = self.env["stock.quant.package"].search([("name", "=", pack_name)])
        company = self.env.user.company_id  # FIXME add logic to get proper company
        # FIXME add logic to get proper warehouse
        warehouse = self.env["stock.warehouse"].search([])[0]
        picking_type = (
            warehouse.int_type_id
        )  # FIXME add logic to get picking type properly
        product = pack.quant_ids[
            0
        ].product_id  # FIXME we consider only one product per pack
        move_vals = {
            "picking_type_id": picking_type.id,
            "product_id": product.id,
            "location_id": pack.location_id.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "name": product.name,
            "product_uom": product.uom_id.id,
            "product_uom_qty": pack.quant_ids[0].quantity,
            "company_id": company.id,
        }
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm()
        self.env["stock.package_level"].create(
            {
                "package_id": pack.id,
                "move_ids": [(6, 0, [move.id])],
                "company_id": company.id,
            }
        )
        move.picking_id.action_assign()
        return_vals = {
            "name": pack.name,
            "location_name": pack.location_id.name,
            "location_dest_name": move.move_line_ids[0].location_dest_id.name,
            "product_name": move.name,
            "picking_name": move.picking_id.name,
            "location_id": pack.location_id.id,
            "location_dest_id": move.move_line_ids[0].location_dest_id.id,
            "move_id": move.id,
            #            'allow_change_destination': True, #TODO
        }
        return return_vals

    def validate(self, move_id, location_name):
        move = self.env["stock.move"].browse(move_id)
        dest_location = self.env["stock.location"].search(
            [("name", "=", location_name)]
        )
        if move.move_line_ids[0].location_dest_id.id != dest_location.id:
            move.move_line_ids[0].location_dest_id = dest_location.id
        move.move_line_ids[0].qty_done = move.move_line_ids[0].product_uom_qty
        move.picking_id.button_validate()
        return True

    def cancel(self, move_id):
        move = self.env["stock.move"].browse(move_id)
        move.picking_id.cancel()
        return True

    def _validator_cancel(self):
        return {"move_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def _validator_validate(self):
        return {
            "move_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_name": {"type": "string", "nullable": False, "required": True},
        }

    def _validator_scan(self):
        return {"pack_name": {"type": "string", "nullable": False, "required": True}}

    def _validator_return_scan(self):
        return {"data": self._record_return_schema}

    def get_by_name(self, pack_name):
        """
        Get pack informations
        """
        pack = self.env["stock.quant.package"].search(
            [("name", "=", pack_name)],
            # TODO, is it what we want? error if not found?
            limit=1,
        )
        return self._to_json(pack)[:1]

    def _validator_get_by_name(self):
        return {"pack_name": {"type": "string", "nullable": False, "required": True}}

    def _validator_return_get_by_name(self):
        return {"data": self._record_return_schema}

    def _convert_one_record(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "location": {"id": record.location_id.id, "name": record.location_id.name},
        }

    @property
    def _record_return_schema(self):
        return {
            "type": "dict",
            "schema": {
                "id": {"coerce": to_int, "required": True, "type": "integer"},
                "name": {"type": "string", "nullable": False, "required": True},
                "location": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
            },
        }
