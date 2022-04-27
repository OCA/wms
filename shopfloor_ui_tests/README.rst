==================
Shopfloor ui tests
==================

Tests for the Shopfloor app.

These are end-to-end & unit tests that cover the frontend of the application.
Not testing the WMS part at this time.

Tech details
~~~~~~~~~~~~

* The end-to-end tests are built using `Cypress <https://www.cypress.io/>`_.
* The unit tests are built using `jest <https://jestjs.io/docs/getting-started>`_.

End-to-end tests with Cypress
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pre-requisites
==============

* You should have npm and Cypress installed.
* You should have the below modules installed:

    - shopfloor_example
    - shopfloor_mobile
    - shopfloor_mobile_base
    - shopfloor_mobile_base_auth_user OR shopfloor_mobile_base_auth_api_key*

    ``*`` These two modules are mutually exclusive so make sure to only install the one needed by the app.

* Your Odoo instance must be running.

Open the Cypress interface
==========================

* In a terminal, go to path/to/shopfloor_ui_tests.
* >> ``npx cypress open``

Select a test
=============

With the Cypress interface open, select your test.
A new browser window will be open and will run the test. 

For more information regarding the Cypress interface, visit `Cypress features <https://www.cypress.io/features/>`_.
If you want to run the test in a specific browser, visit `Cypress browsers <https://docs.cypress.io/guides/guides/launching-browsers#Browsers/>`_.


Test output
===========

* If any of the steps fail, the Test Stateus Menu will highlight it in red and give you relevant information about the issue.
* If all steps of your test are green, you're good to go!

Unit tests with jest
~~~~~~~~~~~~~~~~~~~~

Pre-requisites
==============

* You should have npm installed.

Run your tests
==============
* Navigate to path/to/shopfloor_ui_tests.
* If this is the first time you're running these tests:
    * ``npm install``
* To run all tests:
    * ``npm run unit-tests``

Add new tests
=============

To add a new test, simply create a new `**.test.js` file inside the `unit_tests` folder.

The default environment for these tests uses node.js.
Since we're building a web app, we need to add the "jsdom" environment by pasting the below on top of your test file:

.. code-block:: javascript

    /**
    * @jest-environment jsdom
    */

Known issues / Roadmap
~~~~~~~~~~~~~~~~~~~~~~

Cypress:

* At this stage, the features of the Shopfloor app that are covered by Cypress tests are:
    - Authentication via username and password.
    - Authentication via apikey.
    - Navigation throughout the main pages of the app.
    - Selection and representation of profiles.
    - Module shopfloor_example.

* Test the WMS features from `shopfloor_mobile`.

jest:

* Look into the option of running only a single test, or a series of specific tests.


NOTE: THE TESTS ARE NOT CURRENTLY PART OF THE CI/CD PIPELINE.
