"""
Support actions available from any Service Components.

To use an Action Component, a Service component

Difference with Service components:

* Public methods of a Service Components are exposed in the REST API,
  Action Components are never exposed
* Action Components will generally have an existing Odoo model name

An Action component can be get from Service or Action Components using
``self.actions_for(model_name)``.

The goal of the Action Components is to share common actions
and processes between Services, avoid having too much logic in
Services.

"""
from . import base_action
from . import stock_package_level
