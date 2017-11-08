var taxiIcon = L.icon({
    iconUrl: 'assets/img/taxi.png',
    iconSize: [38, 55], // size of the icon
});
var passengerIcon = L.icon({
    iconUrl: 'assets/img/passenger.png',
    iconSize: [38, 40], // size of the icon
});

$("#generate-btn").on("click", function (e) {
    $.getJSON("/generate", function (data) {
    })
});

$("#move-btn").on("click", function (e) {
    $.getJSON("/move", function (data) {
    })
});


var taxis = {};
var passengers = {};
var paths = {};
var urls = {};

var intervalID = setInterval(function () {
    $.getJSON("/entities", function (data) {
        // draw taxis
        var count = data.taxis.length;
        for (var i = 0; i < count; i++) {
            var taxi = data.taxis[i];
            if (!(taxi.id in taxis))
            {
                //console.log("Creating marker with position " + taxi.position);
                var marker = L.animatedMarker([taxi.position], {
                    icon: taxiIcon
                });
                map.addLayer(marker);
                taxi.marker = marker;
                taxis[taxi.id] = taxi;
            }
            updateTaxi(taxi);
        }
        // draw passengers
        count = data.passengers.length;
        for (i = 0; i < count; i++) {
            var passenger = data.passengers[i];
            if (!(passenger.id in passengers)) {
                //console.log("Creating marker with position " + passenger.position);
                marker = L.animatedMarker([passenger.position], {
                    icon: passengerIcon
                });
                map.addLayer(marker);
                passenger.marker = marker;
                passengers[passenger.id] = passenger;
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
        //localtaxi.marker.destinations = taxi.destinations;
        var polyline = L.polyline(taxi.path, {color: 'blue'});
        polyline.addTo(map);
        map.removeLayer(localtaxi.marker);
        localtaxi.marker = L.animatedMarker(polyline.getLatLngs(), {
            icon: taxiIcon,
            autoStart: false,
            onEnd: function () {
                _polyline = paths[this];
                map.removeLayer(_polyline);
                if (this in urls) {
                    delete urls[this];
                }
            }
        });
        map.addLayer(localtaxi.marker);
        localtaxi.marker.start();
        paths[localtaxi.marker] = polyline;
        urls[localtaxi.marker] = localtaxi.url;
        localtaxi.marker.start();
        localtaxi.dest = taxi.dest;
    }
    // update taxi's position
    if (localtaxi.marker && localtaxi.marker in urls) {
        var coords = localtaxi.marker.getLatLng();
        if (localtaxi.position[0] != coords.lat || localtaxi.position[1] != coords.lng) {
            var url = urls[localtaxi.marker];
            url = url + "/update_position?lat=" + coords.lat + "&lon=" + coords.lng;
            $.getJSON(url);
        }
    }
};
