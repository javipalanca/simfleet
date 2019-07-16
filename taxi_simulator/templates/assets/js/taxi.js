const taxiIcon = L.icon({
    iconUrl: 'assets/img/taxi.png',
    iconSize: [38, 55], // size of the icon
});
const passengerIcon = L.icon({
    iconUrl: 'assets/img/passenger.png',
    iconSize: [38, 40], // size of the icon
});

const passenger2Icon = L.icon({
    iconUrl: 'assets/img/passenger2.png',
    iconSize: [38, 40], // size of the icon
    className: "fadeOut",
});

const stationIcon = L.icon({
   iconUrl: 'assets/img/tomacorriente.png',
   iconSize: [38,40]
});

const backend_port = $("#backport").val();
const ip_address = $("#ip_address").val();

$("#generate-btn").on("click", function (e) {
    var numtaxis = $("#numtaxis").val();
    var numpassengers = $("#numpassengers").val();
    if (numtaxis === "") {
        numtaxis = 0;
    }
    if (numpassengers === "") {
        numpassengers = 0;
    }
    $.getJSON("http://"+ ip_address +":" + backend_port + "/generate/taxis/" + numtaxis + "/passengers/" + numpassengers,
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

let taxis = {};
let passengers = {};
let paths = new HashTable();
let urls = new HashTable();
let stations = {}

/*const CUSTOMER_WAITING = 20;
const CUSTOMER_IN_TRANSPORT = 21;
const CUSTOMER_IN_DEST = 22;
const CUSTOMER_ASSIGNED = 24;
*/
const CUSTOMER_WAITING = "CUSTOMER_WAITING";
const CUSTOMER_IN_TRANSPORT = "CUSTOMER_IN_TRANSPORT";
const CUSTOMER_IN_DEST = "CUSTOMER_IN_DEST";
const CUSTOMER_ASSIGNED = "CUSTOMER_ASSIGNED";

const statuses = {
    10: "TRANSPORT_WAITING",
    11: "TRANSPORT_MOVING_TO_CUSTOMER",
    12: "TRANSPORT_IN_CUSTOMER_PLACE",
    13: "TRANSPORT_MOVING_TO_DESTINATION",
    14: "TRANSPORT_WAITING_FOR_APPROVAL",
    //
    20: "CUSTOMER_WAITING",
    21: "CUSTOMER_IN_TRANSPORT",
    22: "CUSTOMER_IN_DEST",
    23: "CUSTOMER_LOCATION",
    24: "CUSTOMER_ASSIGNED"
};

color = {
    11: "blue",
    13: "green",
    "TRANSPORT_MOVING_TO_CUSTOMER": "blue",
    "TRANSPORT_MOVING_TO_DESTINATION": "green",
};

function gen_passenger_popup(passenger) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + passenger.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + passenger.status + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + passenger.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + passenger.dest + "</td></tr>" +
        "<tr><th>TRANSPORT</th><td>" + passenger.taxi + "</td></tr>" +
        "<tr><th>WAITING</th><td>" + passenger.waiting + "</td></tr>" +
        "</table>"
}

function gen_taxi_popup(taxi) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + taxi.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + taxi.status + "</td></tr>" +
        "<tr><th>CUSTOMER</th><td>" + taxi.passenger + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + taxi.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + taxi.dest + "</td></tr>" +
        "<tr><th>ASSIGNMENTS</th><td>" + taxi.assignments + "</td></tr>" +
        "<tr><th>SPEED</th><td>" + taxi.speed + "</td></tr>" +
        "<tr><th>DISTANCE</th><td>" + taxi.distance + "</td></tr>" +
        "</table>"
}

function station_popup(station) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + station.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + station.status + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + station.position + "</td></tr>"
        "</table>"
}


var tree = JSON.stringify({});
var $tree = $('#tree');
var $waiting = $('#waiting');
var $total = $('#total');
var newtree;

/**********************************/
var animateTaxi = function (marker, speed) {
    // Only if CSS3 transitions are supported
    if (L.DomUtil.TRANSITION) {
        if (marker._icon) {
            marker._icon.style[L.DomUtil.TRANSITION] = ('all ' + speed + 'ms linear');
        }
        if (marker._shadow) {
            marker._shadow.style[L.DomUtil.TRANSITION] = 'all ' + speed + 'ms linear';
        }
    }
};

var updateTaxi = function (taxi) {
    var localtaxi = taxis[taxi.id];
    // check if there is a new route for the taxi
    if (taxi.dest != null && !taxi.dest.equals(localtaxi.dest) && taxi.path) {
        localtaxi.path = taxi.path;
        localtaxi.dest = taxi.dest;
        var polyline = L.polyline(taxi.path, {color: color[taxi.status]});
        polyline.addTo(map);
        paths.put(localtaxi.marker, polyline);
        localtaxi.dest = taxi.dest;
    }
    // update taxi's position
    if (localtaxi.marker) {
        var coords = [taxi.position[0], taxi.position[1]];
        animateTaxi(localtaxi.marker, taxi.speed);
        localtaxi.marker.setLatLng(coords);
        if ((taxi.dest != null) && (taxi.position[0] === localtaxi.dest[0] && taxi.position[1] === localtaxi.dest[1])) {
            // taxi is in destiny
            var _polyline = paths.get(localtaxi.marker);
            map.removeLayer(_polyline);
        }

    }
    localtaxi.marker._popup.setContent(gen_taxi_popup(taxi));
};

/**********************************/

//var intervalID = setInterval(function () {
var animate = function () {
    $.getJSON("/entities", function (data) {
        // update tree
        newtree = JSON.stringify(data.tree);
        if (newtree !== tree) {
            tree = newtree;
            $tree.treeview({data: tree, showTags: true});
        }
        // update stats
        $waiting.html(data.stats.waiting);
        $total.html(data.stats.totaltime);


        // draw taxis
        var count = data.taxis.length;
        for (var i = 0; i < count; i++) {
            var taxi = data.taxis[i];
            if (!(taxi.id in taxis)) {
                var marker = L.marker(taxi.position, {
                    icon: taxiIcon,
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
                (passenger.status === CUSTOMER_WAITING || passenger.status === CUSTOMER_ASSIGNED)) {
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
                if (passenger.status === CUSTOMER_IN_TRANSPORT || passenger.status === CUSTOMER_IN_DEST) {
                    if (localpassenger && "marker" in localpassenger) {
                        map.removeLayer(localpassenger.marker);
                    }
                }
            }
            if (localpassenger && "marker" in localpassenger && "_popup" in localpassenger.marker) {
                localpassenger.marker._popup.setContent(gen_passenger_popup(passenger))
            }
        }
        // draw stations
        count = data.stations.length;
        for (i = 0; i < count; i++) {
            var station = data.stations[i];
            if (!(station.id in stations)) {
                marker = L.marker(station.position, {
                    icon: stationIcon,
                    clickable: true
                });
                map.addLayer(marker);
                station.marker = marker;
                station.marker.bindPopup(station_popup(station));
                stations[station.id] = station;
            }
        }
    });
    setTimeout(animate, 100);
};
animate();
