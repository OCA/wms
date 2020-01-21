from odoo.addons.component.core import Component


class ShopfloorService(Component):
    _inherit = "base.rest.service"
    _name = "shopfloor.service"
    _collection = "shopfloor.services"
    _usage = "shopfloor"

    def get_pack(self, pack_name):
        """
        Get pack informations
        """
        pack = self.env['stock.quant.package'].search([('name', '=', pack_name)])
        return self._to_json(pack)

    def _validator_get_pack(self):
        return {"pack_name": {"type": "string", "nullable": False, "required": True}}

    def _to_json(self, pack):
        res = {
            "id": pack.id,
            "name": pack.name,
            "location": pack.location_id.name,
        }
        return res
