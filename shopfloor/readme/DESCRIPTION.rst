Shopfloor is a barcode scanner application for internal warehouse operations.

The application supports scenarios, to relate to Operation Types:

* Cluster Picking
* Zone Picking
* Checkout/Packing
* Delivery
* Location Content Transfer
* Single Pack Transfer

This module provides REST APIs to support the scenarios. It needs a frontend
to consume the backend APIs and provide screens for users on barcode devices.
A default front-end application is provided by ``shopfloor_mobile``.

| Note: if you want to enable a new scenario on an existing application, you must trigger the registry sync on the shopfloor.app in a post_init_hook or a post-migrate script.
| See an example `here <https://github.com/OCA/wms/pull/520/commits/bccdfd445a9bc943998c4848f183a076e8459a98>`_.
