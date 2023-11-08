# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from contextlib import closing

from .common import CommonCase


class ActionsLockCase(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.partner = cls.env.ref("base.res_partner_12")
        with cls.work_on_actions(cls) as work:
            cls.lock = work.component(usage="lock")

    def test_select_for_update_skip_locked_ok(self):
        """Check the lock is obtained and True is returned."""
        result = self.lock.for_update(self.partner, skip_locked=True)
        self.assertTrue(result)

    def test_select_for_update_skip_locked_not_ok(self):
        """Check the lock is NOT obtained and False is returned."""
        with closing(self.registry.cursor()) as cr:
            # Simulate another user locked a row
            cr.execute(
                "SELECT id FROM res_partner WHERE id=%s FOR UPDATE", (self.partner.id,)
            )
            result = self.lock.for_update(self.partner, skip_locked=True)
            self.assertFalse(result)
