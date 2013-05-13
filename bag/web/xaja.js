'use strict';
/*jslint browser: true, devel: true */

String.prototype.interpol = function () {
    // String interpolation for format strings like "Item [0] of [1]".
    // May receive strings or numbers as arguments.
    var args = arguments;
    try {
        return this.replace(/\[(\d+)\]/g, function () {
            // The replacement string is given by the nth element in the list,
            // where n is the second group of the regular expression:
            return args[arguments[1]];
        });
    } catch (e) {
        if (window.console) { console.log(['Exception on interpol() called on',
            this, 'with arguments', arguments]); }
        throw (e);
    }
};


var xaja = {  // Make AJAX requests without worrying about errors
    get: function (o) { // args: url, data, done, dataType, error
        this.request(o, 'GET');
    },
    post: function (o) {
        this.request(o, 'POST');
    },
    put: function (o) {
        this.request(o, 'PUT');
    },
    delete: function (o) {
        this.request(o, 'DELETE');
    },
    request: function (o, method) {
        var onDone = function (data, textStatus, xhr) {
            xaja.dispatch(data, textStatus, xhr, o);
        };
        o.success = onDone;
        o.data = o.data || '';
        o.type = method;
        $.ajax(o);
    },
    dispatch: function (data, textStatus, xhr, o) {
        if (data.error_msg) {
            alert("Server error:\n" + data.error_msg);
            if (o.error) { o.error(data, textStatus, xhr); }
        } else {
            if (o.done) { o.done(data, textStatus, xhr); }
        }
    }
};


$.ajaxSetup({
    error: function (xhr, exception) {
        if (xhr.status === 0) {
            alert("Operation canceled: could not connect to the server.");
        } else if (xhr.status === 404) {
            alert('404 Resource not found.');
        } else if (xhr.status === 500) {
            alert('500 Internal server error.\n' + xhr.responseText);
            // top.location.href = "/account/logout";
        } else if (exception === 'parsererror') {
            if (window.console) { console.log(xhr); }
            alert('Oh dear, the server returned an invalid response!');
            // top.location.href = "/account/logout";
        } else if (exception === 'timeout') {
            alert('A request to the server has timed out.');
        } else if (exception === 'abort') {
            alert('The request has been canceled.');
        } else {
            if (window.console) { console.log(xhr); }
            alert('Ops, this error has not been treated on the client:\n'
                + xhr.responseText);
        }
    }
});
