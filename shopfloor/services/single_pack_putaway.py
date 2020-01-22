from odoo.addons.component.core import Component


class SinglePackPutaway(Component):
    """Methods for the Single Pack Put-Away Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.putaway"
    _usage = "single_pack_putaway"
    _description = __doc__
