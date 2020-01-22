from odoo.addons.component.core import Component


class SinglePackTransfer(Component):
    """Methods for the Single Pack Transfer Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.transfer"
    _usage = "single_pack_transfer"
    _description = __doc__
