* Split module by scenario
* Improve documentation and demo data
* Document each component
* Document demo mode
* Find / create a nice icon
* Finish base translations (move all UI strings to translatable terms)
* Use SCSS
* Refactor states definition

  States are now part of the scenario data. They should be specific objects with their own class.
  They should also provide all the actions that should be displayed w/ their handlers when needed.
  Actions can be popup actions or buttons at the bottom of the screen.
  The tricky part here could be how to register this states for the given component.
  Today states have access to the full object of the scenario component as they are part of it.
  `_get_state_spec` could probably lookup for registered states
  (eg: when you register a component in the registry you should provide states as well).
  When we'll have states in this fashion we should also consider if they should provide their own template.
  This way the component template will hold only the generic bits of the scenario.

* Back buttons should be smarter

  In some cases getting back using history is fine but very often this could lead to outdated data display.
  To mitigate this in particular scenario's steps, custom handlers for the back action have been implemented.
  For instance, in cluster_picking when you hit back on manual selection it forces the state to go to start and reload.
  For starting we should provide `on_back` property to all states where we want to display it
  (no more specific check on the state to display this button).
  This part is also related to "Refactor states definition".

* Load modules/components dependencies

  As of today we are using bare ES6 imports which requires devs to know the exact path
  of the resource. If the resource changes name or path dependent files will be broken.
  It would be nice to have a way to declare modules by name as Odoo JS does.

* Get rid of custom assets controller?

  A controller takes care of loading static assets but seems to not be needed anymore.
