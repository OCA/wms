from contextlib import contextmanager

from odoo.tests.common import SavepointCase

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext


class CommonCase(SavepointCase):
    @contextmanager
    def work_on_services(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.service", self.env)
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )
