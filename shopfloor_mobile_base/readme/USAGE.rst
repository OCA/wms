Pre-requisites
~~~~~~~~~~~~~~

* Your Odoo instance is accessible via mobile device
* You have an API Key configured

Start the app
~~~~~~~~~~~~~

* Go to "Inventory -> Configuration -> Shopfloor -> Shopfloor App"
* In the login screen fill in your API key
* Hit "Login"

Select a profile
~~~~~~~~~~~~~~~~

Several profiles can be configured in the backend,
you must choose one before starting.

* Tap on "Configure profile"
* Select a profile

This will load all available menu items for the selected profile.

Change language
~~~~~~~~~~~~~~~

* Go to "Settings -> Language"
* Select a language

Customization
~~~~~~~~~~~~~

Please refer to `shopfloor_mobile_custom_example`.


Working environment
~~~~~~~~~~~~~~~~~~~

You can control which running env is considerd by Odoo config or env vars.


For Odoo config: `running_env` or `shopfloor_running_env`.

For env var: `RUNNING_ENV` or `SHOPFLOOR_RUNNING_ENV`.

Expected key `RUNNING_ENV` is compliant w/ `server_environment` naming but is not depending on it.

Additionally, as specific key for Shopfloor is supported.

**You don't need `server_environment` module to use this feature.**
