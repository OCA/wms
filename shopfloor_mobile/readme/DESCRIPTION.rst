Frontend for Shopfloor app.

The work is organized in scenario.
A scenario represents a process in the warehouse (eg: receive, deliver).
The app allows to start each process through the main menu.

Each scenario is linked to a specific menu item which can be configured in the backend.
Each scenario drives you through the work to do.


Tech details
~~~~~~~~~~~~

* This frontend is built on top of `VueJS <vuejs.org>`_  and `VuetifyJS <vuetifyjs.com/>`_
  and relies on `shopfloor` module that exposes REST API in Odoo
  (based in turn on `base_rest <https://github.com/OCA/rest-framework/tree/13.0/base_rest>`_).

* The whole business logic comes from `shopfloor` module,
  this module takes care of providing a nice and reactive UI to work with.

* No Odoo JS is used, no assets machinery used.

  Static assets are loaded straight, served by a specific controller.
  This app is a Single Page App, hence resources are loaded only once.

  The version of the module appended to the URL of each resources
  makes sure it's not cached when the version changes.

* When developing you can use a demo mode which allows to define interactive scenario
  with pure JS demo data, without interacting with Odoo.
  Nothing to deal with Odoo demo data.
