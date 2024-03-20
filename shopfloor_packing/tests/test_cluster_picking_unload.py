# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.test_cluster_picking_unload import (
    ClusterPickingPrepareUnloadCase,
    ClusterPickingSetDestinationAllCase,
    ClusterPickingUnloadScanDestinationCase,
    ClusterPickingUnloadScanPackCase,
    ClusterPickingUnloadSplitCase,
)


class ClusterPickingPrepareUnloadCase2(ClusterPickingPrepareUnloadCase):
    """
    Ensure that the normal unload process is preserved if the pack_pickings option.

    is not activated on the menu (default)
    """


class ClusterPickingSetDestinationAllCase2(ClusterPickingSetDestinationAllCase):
    """
    Ensure that the normal unload process is preserved if the pack_pickings option.

    is not activated on the menu (default)
    """


class ClusterPickingUnloadSplitCase2(ClusterPickingUnloadSplitCase):
    """
    Ensure that the normal unload process is preserved if the pack_pickings option.

    is not activated on the menu (default)
    """


class ClusterPickingUnloadScanPackCase2(ClusterPickingUnloadScanPackCase):
    """
    Ensure that the normal unload process is preserved if the pack_pickings option.

    is not activated on the menu (default)
    """


class ClusterPickingUnloadScanDestinationCase2(ClusterPickingUnloadScanDestinationCase):
    """
    Ensure that the normal unload process is preserved if the pack_pickings option.

    is not activated on the menu (default)
    """
