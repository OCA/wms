from odoo.addons.component.core import Component


# TODO move in a pack service
class ShopfloorService(Component):
    _inherit = "base.shopfloor.service"
    _name = "shopfloor.service"
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
