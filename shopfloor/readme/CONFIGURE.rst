Profiles
~~~~~~~~

In Inventory / Configuration / Shopfloor / Profiles.

The profiles are used to restrict which menus are shown on the frontend
application. When a user logs in the scanner application, they have to
select their profile, so the correct menus are shown.

Menus
~~~~~

In Inventory / Configuration / Shopfloor / Menus.

The menus are displayed on the frontend application and store the configuration
of the scenarios. Each menu must use a scenario and defines which Operation Types
they are allowed to process.

Their profile will restrict the visibility to the profile chosen on the device.
If a menu has no profile, it is shown in every profile.

Some scenarios may have additional options, which are explained in tooltips.

Logs retention
~~~~~~~~~~~~~~

Logs are kept in database for every REST requests made by a client application.
They can be used for debugging and monitoring of the activity.

The Logs menu is shown only with Developer tools (``?debug=1``) activated.

By default, Shopfloor logs are kept 30 days.
You can change the duration of the retention by changing the System Parameter
``shopfloor.log.retention.days``.

If the value is set to 0, the logs are not stored at all.

Logged data is: request URL and method, parameters, headers, result or error.
