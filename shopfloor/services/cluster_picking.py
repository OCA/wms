from odoo.addons.component.core import Component


class ClusterPicking(Component):
    """Methods for the Cluster Picking Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.cluster.picking"
    _usage = "cluster_picking"
    _description = __doc__
