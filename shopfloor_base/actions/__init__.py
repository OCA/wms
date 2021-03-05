"""
Support actions available from any Service Components.

To use an Action Component, a Service component

Difference with Service components:

* Public methods of a Service Components are exposed in the REST API,
  Action Components are never exposed

An Action component can be get from Service or Action Components using
``self._actions_for(usage)``.

The goal of the Action Components is to share common actions
and processes between Services, avoid having too much logic in
Services.

"""
from . import base_action
from . import data
from . import data_detail
from . import schema
from . import schema_detail
from . import message
from . import search
from . import savepoint

# TODO: kept in shopfloor -> review if these must stay there
# from . import change_package_lot
# from . import schema_detail
# from . import completion_info
# from . import location_content_transfer_sorter
# from . import move_line_search
# from . import stock
# from . import inventory
