/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/* eslint-disable valid-jsdoc */
/* eslint-disable no-implicit-globals */
/* eslint-disable strict */

// Credit https://stackoverflow.com/questions/43792026

window._standardFetch = fetch;

window.standardFetch = function () {
    var fetchUnauthorized = new Event("fetchUnauthorized", {
        view: document,
        bubbles: true,
        cancelable: false,
    });

    // Pass the supplied arguments to the real fetch function
    var fetchCall = window._standardFetch.apply(this, arguments);

    const _check_unauthorized = (data) => {
        if (data.status === 401) {
            fetchUnauthorized.data = {
                body: data.body,
                url: data.url,
                status: data.status,
                status_text: data.statusText,
            };
            document.dispatchEvent(fetchUnauthorized);
        }
    };

    fetchCall.then(function (data) {
        // Check if the user is unauthorized
        // and trigger the fetchUnauthorized event
        _check_unauthorized(data);
    });
    return fetchCall;
};

/**
 * Patch `fetch` to trigger events on start and end request.
 */
window.fetch = function () {
    // Create hooks
    var fetchStart = new Event("fetchStart", {
        view: document,
        bubbles: true,
        cancelable: false,
    });
    var fetchEnd = new Event("fetchEnd", {
        view: document,
        bubbles: true,
        cancelable: false,
    });

    // Pass the supplied arguments to the real fetch function
    var fetchCall = window.standardFetch.apply(this, arguments);

    // Trigger the fetchStart event
    document.dispatchEvent(fetchStart);

    fetchCall
        .then(function () {
            // Trigger the fetchEnd event
            document.dispatchEvent(fetchEnd);
        })
        .catch(function () {
            // Trigger the fetchEnd event
            document.dispatchEvent(fetchEnd);
        });

    return fetchCall;
};
