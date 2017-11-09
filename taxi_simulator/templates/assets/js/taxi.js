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

$("#generate-btn").on("click", function (e) {
    var numtaxis = $("#numtaxis").val();
    var numpassengers = $("#numpassengers").val();
    if (numtaxis === "") { numtaxis = 0;}
    if (numpassengers === "") { numpassengers = 0;}
    $.getJSON("/generate?taxis="+numtaxis+"&passengers="+numpassengers, function (data) {
    })
});

$("#clean-btn").on("click", function (e) {
    $.getJSON("/clean", function (data) {
        for (var taxi in taxis){
            if (taxi.marker !== undefined)
                map.removeLayer(taxi.marker);
        }
        for (var passenger in passengers){
            if (passenger.marker !== undefined)
                map.removeLayer(passenger.marker);
        }
        taxis = {};
        passengers = {};
        paths = new HashTable();
        urls = new HashTable();
    })
});


var taxis = {};
var passengers = {};
var paths = new HashTable();
var urls = new HashTable();

var PASSENGER_WAITING = 20;
var PASSENGER_IN_TAXI = 21;
var PASSENGER_IN_DEST = 22;

color = {
    11: "blue",
    13: "green"
};

var intervalID = setInterval(function () {
    $.getJSON("/entities", function (data) {
        // draw taxis
        var count = data.taxis.length;
        for (var i = 0; i < count; i++) {
            var taxi = data.taxis[i];
            if (!(taxi.id in taxis))
            {
                var marker = L.animatedMarker([taxi.position], {
                    icon: taxiIcon,
                    distance: 600,  // meters
                    interval: 1000 // milliseconds
                });
                map.addLayer(marker);
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
            if (!(passenger.id in passengers) && (passenger.status === PASSENGER_WAITING)) {
                //console.log("Creating marker with position " + passenger.position);
                marker = L.marker(passenger.position, {
                    icon: passengerIcon
                });
                map.addLayer(marker);
                passenger.marker = marker;
                passengers[passenger.id] = passenger;
            }
            else {
                localpassenger = passengers[passenger.id];
                if (passenger.status === PASSENGER_IN_TAXI) {
                    map.removeLayer(localpassenger.marker);
                }
                /*else if ((passenger.id in passengers) && passenger.status === PASSENGER_IN_DEST) {
                    marker = L.animatedMarker([passenger.position], {
                        icon: passenger2Icon
                    });
                    map.addLayer(marker);
                    delete passengers[passenger.id];
                }*/
            }
        }
    });
}, 1000);


/**********************************/

var updateTaxi = function (taxi) {
    var localtaxi = taxis[taxi.id];
    // check if there is a new route for the taxi
    if (taxi.dest != null && !taxi.dest.equals(localtaxi.dest)) {
        localtaxi.path = taxi.path;
        localtaxi.dest = taxi.dest;
        var polyline = L.polyline(taxi.path, {color: color[taxi.status]});
        polyline.addTo(map);
        map.removeLayer(localtaxi.marker);
        localtaxi.marker = L.animatedMarker(polyline.getLatLngs(), {
            icon: taxiIcon,
            autoStart: true,
            onEnd: function () {
                var _polyline = paths.get(this);
                map.removeLayer(_polyline);
                var url = urls.get(this);
                url = url + "/arrived";
                $.getJSON(url).error(function (e) {
                    // retry
                    $.getJSON(url);
                });
                urls.put(this, undefined);
            }
        });
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
            $.getJSON(url);
        }
    }
};
