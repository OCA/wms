from .common import CommonCase


class ClusterPickingCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.process.picking_type_ids

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="cluster_picking")
