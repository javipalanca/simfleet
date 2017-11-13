var taxiIcon = L.icon({
    iconUrl: 'assets/img/taxi.png',
    iconSize: [38, 55], // size of the icon
});
var passengerIcon = L.icon({
    iconUrl: 'assets/img/passenger.png',
    iconSize: [38, 40], // size of the icon
});

var passenger2Icon = L.icon({
    iconUrl: 'assets/img/passenger2.png',
    iconSize: [38, 40], // size of the icon
    className: "fadeOut",
});

var backend_port = $("#backport").val();

$("#generate-btn").on("click", function (e) {
    var numtaxis = $("#numtaxis").val();
    var numpassengers = $("#numpassengers").val();
    if (numtaxis === "") {
        numtaxis = 0;
    }
    if (numpassengers === "") {
        numpassengers = 0;
    }
    $.getJSON("http://127.0.0.1:" + backend_port + "/generate/taxis/" + numtaxis + "/passengers/" + numpassengers,
        function (data) {
        });
});

$("#play-btn").on("click", function (e) {
    $.getJSON("/run");
});

function request_url(url) {
    $.getJSON(url, function (result) {
        if (!result.finished) {
            setTimeout(request_url, 2000);
        }
    });
}

var taxis = {};
var passengers = {};
var paths = new HashTable();
var urls = new HashTable();

var PASSENGER_WAITING = 20;
var PASSENGER_IN_TAXI = 21;
var PASSENGER_IN_DEST = 22;
var PASSENGER_ASSIGNED = 24;

var statuses = {
    10: "TAXI_WAITING",
    11: "TAXI_MOVING_TO_PASSENGER",
    12: "TAXI_IN_PASSENGER_PLACE",
    13: "TAXI_MOVING_TO_DESTINY",
    14: "TAXI_WAITING_FOR_APPROVAL",
    //
    20: "PASSENGER_WAITING",
    21: "PASSENGER_IN_TAXI",
    22: "PASSENGER_IN_DEST",
    23: "PASSENGER_LOCATION",
    24: "PASSENGER_ASSIGNED"
};

color = {
    11: "blue",
    13: "green"
};

function gen_passenger_popup(passenger) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + passenger.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + statuses[passenger.status] + "</td></tr>" +
        "<tr><th>TAXI</th><td>" + passenger.taxi + "</td></tr>" +
        "<tr><th>WAITING</th><td>" + passenger.waiting + "</td></tr>" +
        "</table>"
}

function gen_taxi_popup(taxi) {
        return "<table class='table'><tbody><tr><th>NAME</th><td>" + taxi.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + statuses[taxi.status] + "</td></tr>" +
        "<tr><th>PASSENGER</th><td>" + taxi.passenger + "</td></tr>" +
        "<tr><th>ASSIGNMENTS</th><td>" + taxi.assignments + "</td></tr>" +
        "<tr><th>DISTANCE</th><td>" + taxi.distance + "</td></tr>" +
        "</table>"
}

var intervalID = setInterval(function () {
    $.getJSON("/entities", function (data) {
        // draw taxis
        var count = data.taxis.length;
        for (var i = 0; i < count; i++) {
            var taxi = data.taxis[i];
            if (!(taxi.id in taxis)) {
                var marker = L.animatedMarker([taxi.position], {
                    icon: taxiIcon,
                    distance: 600,  // meters
                    interval: 1000, // milliseconds
                    clickable: true
                });
                map.addLayer(marker);
                marker.bindPopup("");
                taxi.marker = marker;
                taxis[taxi.id] = taxi;
            }
            updateTaxi(taxi);
        }
        // draw passengers
        count = data.passengers.length;
        var localpassenger;
        for (i = 0; i < count; i++) {
            var passenger = data.passengers[i];
            if (!(passenger.id in passengers) &&
                (passenger.status === PASSENGER_WAITING || passenger.status === PASSENGER_ASSIGNED)) {
                marker = L.marker(passenger.position, {
                    icon: passengerIcon
                });
                map.addLayer(marker);
                passenger.marker = marker;
                passenger.marker.bindPopup(gen_passenger_popup(passenger));
                passengers[passenger.id] = passenger;
                localpassenger = passengers[passenger.id];
            }
            else {
                localpassenger = passengers[passenger.id];
                if (passenger.status === PASSENGER_IN_TAXI || passenger.status === PASSENGER_IN_DEST) {
                    if (localpassenger && "marker" in localpassenger) {
                        map.removeLayer(localpassenger.marker);
                    }
                }
            }
            if (localpassenger && "marker" in localpassenger && "_popup" in localpassenger.marker) {
                localpassenger.marker._popup.setContent(gen_passenger_popup(passenger))
            }
        }
    });
}, 1000);


/**********************************/

var updateTaxi = function (taxi) {
    var localtaxi = taxis[taxi.id];
    // check if there is a new route for the taxi
    if (taxi.dest != null && !taxi.dest.equals(localtaxi.dest) && taxi.path) {
        localtaxi.path = taxi.path;
        localtaxi.dest = taxi.dest;
        var polyline = L.polyline(taxi.path, {color: color[taxi.status]});
        polyline.addTo(map);
        map.removeLayer(localtaxi.marker);
        localtaxi.marker = L.animatedMarker(polyline.getLatLngs(), {
            icon: taxiIcon,
            autoStart: true,
            clickable: true,
            onEnd: function () {
                var _polyline = paths.get(this);
                map.removeLayer(_polyline);
                var url = urls.get(this);
                url = url + "/arrived";
                request_url(url);
                urls.put(this, undefined);
            }
        });
        localtaxi.marker.bindPopup(gen_taxi_popup(taxi));
        map.addLayer(localtaxi.marker);
        paths.put(localtaxi.marker, polyline);
        urls.put(localtaxi.marker, localtaxi.url);
        localtaxi.dest = taxi.dest;
    }
    // update taxi's position
    if (localtaxi.marker && urls.get(localtaxi.marker) != undefined) {
        var coords = localtaxi.marker.getLatLng();
        if (localtaxi.position[0] != coords.lat || localtaxi.position[1] != coords.lng) {
            var url = urls.get(localtaxi.marker);
            url = url + "/update_position?lat=" + coords.lat + "&lon=" + coords.lng;
            request_url(url);
        }
    }
    localtaxi.marker._popup.setContent(gen_taxi_popup(taxi));
};
