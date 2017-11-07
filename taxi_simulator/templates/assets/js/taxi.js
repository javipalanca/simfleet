var taxiIcon = L.icon({
    iconUrl: 'assets/img/taxi.png',

    iconSize: [38, 55], // size of the icon
    //iconAnchor: [22, 94], // point of the icon which will correspond to marker's location
    //popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
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
var paths = {};
var urls = {};

var intervalID = setInterval(function () {
    $.getJSON("/entities", function (data) {
        var count = data.taxis.length;
        for (var i = 0; i < count; i++) {
            var taxi = data.taxis[i];
            if (taxi.id in taxis) {
                var localtaxi = taxis[taxi.id];
                updateTaxi(taxi);
            }
            else {
                console.log("Creating marker with position " + taxi.position);
                var marker = L.animatedMarker([taxi.position], {
                    icon: taxiIcon,
                    //destinations: [{latLng: taxi.position}]
                });
                //marker.addTo(map);
                map.addLayer(marker);
                taxi.marker = marker;
                taxis[taxi.id] = taxi;
                if (taxi.dest && taxi.path) {
                    updateTaxi(taxi);
                }
            }
        }
    });
}, 1000);


/**********************************/

var updateTaxi = function (taxi) {
    var localtaxi = taxis[taxi.id];
    //console.log("Updating taxi " + taxi.id);
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
    if (localtaxi.marker && localtaxi.marker in urls) {
        var url = urls[localtaxi.marker];
        var coords = localtaxi.marker.getLatLng();
        url = url + "/update_position?lat=" + coords.lat + "&lon=" + coords.lng;
        $.getJSON(url);
    }
};
