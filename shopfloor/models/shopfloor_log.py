# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models

# TODO: drop this model on next release.
# The feature has been moved to `rest_log`.
#
# It has been tried several times
# to drop the class altogether w/ its related records in this module
# but the ORM is uncapable do delete many records directly relate to the model
# (selection fields values, server actions for crons, etc.)
# and the upgrade will be always broken
# because the model is not in the registry anymore.
#
# Example of the error:
# [2021-02-01 08:44:52,103 1 INFO odoodb ]odoo.addons.base.models.ir_model:
#     Deleting 2617@ir.model.fields.selection
#         (shopfloor.selection__shopfloor_log__severity__severe)
# 2021-02-01 08:44:52,107 1 WARNING odoodb odoo.modules.loading:
#     Transient module states were reset
# 2021-02-01 08:44:52,110 1 ERROR odoodb odoo.modules.registry:
#     Failed to load registry
# Traceback (most recent call last):
#   File "/odoo/src/odoo/modules/registry.py", line 86, in new
#     odoo.modules.load_modules(registry._db, force_demo, status, update_module)
#   File "/odoo/src/odoo/modules/loading.py", line 472, in load_modules
#     env['ir.model.data']._process_end(processed_modules)
#   File "/odoo/src/odoo/addons/base/models/ir_model.py", line 2012, in _process_end
#     record.unlink()
#   File "/odoo/src/odoo/addons/base/models/ir_model.py", line 1206, in unlink
#     not self.env[selection.field_id.model]._abstract:
#   File "/odoo/src/odoo/api.py", line 463, in __getitem__
#     return self.registry[model_name]._browse(self, (), ())
#   File "/odoo/src/odoo/modules/registry.py", line 177, in __getitem__
#     return self.models[model_name]
# KeyError: 'shopfloor.log'


class ShopfloorLog(models.Model):
    _name = "shopfloor.log"
    _description = "Legacy model for tracking REST calls: replacedy by rest.log"
