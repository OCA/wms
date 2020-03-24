from .common import CommonCase


class MenuCase(CommonCase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="menu")

    def test_menu_search(self):
        """Request /menu/search"""
        # Simulate the client searching menus
        response = self.service.dispatch("search")
        menus = self.env["shopfloor.menu"].search([])
        self.assert_response(
            response,
            data={
                "size": len(menus),
                "records": [
                    {
                        "id": menu.id,
                        "name": menu.name,
                        "process": {
                            "id": menu.process_id.id,
                            "code": menu.process_id.code,
                        },
                    }
                    for menu in menus
                ],
            },
        )
