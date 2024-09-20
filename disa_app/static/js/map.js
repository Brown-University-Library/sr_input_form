// if being referred by a People Detail page, the URL will have queries in it
/*const current = new URL(window.location.href);
function hasQueryParams(current) {
    return current.includes('?');
    // break the lat, lon, and zoom out from the URL
    function getQueryStringValue(key) {
        return decodeURIComponent(window.location.search.replace(new RegExp("^(?:.*[&\\?]" + encodeURIComponent(key).replace(/[\.\+\*]/g, "\\$&") + "(?:\\=([^&]*))?)?.*$", "i"), "$1"));
    }
    let querylat = getQueryStringValue("lat");
    let querylon = getQueryStringValue("lon");
    let queryzoom = getQueryStringValue("zoom");
}

let cameFrom = new URL(document.referrer);
if (cameFrom == undefined) { let cameFrom = "" }
// if referrer was a people page, set map with query coordinates, else set default map
if (cameFrom.pathname.startsWith("/people/")) {
    let map = L.map('map-container').setView([querylat, querylon], queryzoom);
} else {
    let map = L.map('map-container').setView([41, -71], 5);
}*/
// establish the default map container
let map = L.map('map-container').setView([41, -71], 5);
//the various basemaps
const basemaps = {
    Standard: L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }),
    Watercolor: L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg', {
        attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ext: 'jpg'
    }),
    Sketch: L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/about" target="_blank">OpenStreetMap</a> contributors',
    })
};
basemaps.Watercolor.addTo(map);

// create marker cluster group and subgroups for feedrom statuses
var mcg = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 30
    }),
    unfree = L.featureGroup.subGroup(mcg),
    free = L.featureGroup.subGroup(mcg),
    unmarked = L.featureGroup.subGroup(mcg),

        // century chunks
    c16 = L.featureGroup.subGroup(mcg),
    c17 = L.featureGroup.subGroup(mcg),
    c18 = L.featureGroup.subGroup(mcg),
    c19 = L.featureGroup.subGroup(mcg),
undated = L.featureGroup.subGroup(mcg);
mcg.addTo(map);
// Adding to map now adds all child layers into the parent group.
free.addTo(map);
unfree.addTo(map);
unmarked.addTo(map);

c16.addTo(map);
c17.addTo(map);
c18.addTo(map);
c19.addTo(map);
undated.addTo(map);

// fetch the geojson
var geoJsonData = new L.GeoJSON.AJAX(
    leaflet_data_url, {

        // build each point
        onEachFeature: function(feature, layer) {

            //var uuid = feature.properties.Referent_ID;
            var person_name = feature.properties.Name;
            if (person_name == " ") {
                var person_name = "A person whose name we do not know"
            }
            var status = feature.properties.Status;
            if (feature.properties.Year) {
                var person_date = feature.properties.Year;
            } else {
                var person_date = "";
            }
            var lat = feature.properties.lat;
            var lng = feature.properties.lon;
            var person_location = feature.properties.from;

            var popupText = person_name + '<br />' + person_location + ', ' + person_date;
            layer.bindPopup(popupText);
            // add to the appropriate subgroup for dynamic filtering
            if (status.startsWith("free")) {
                layer.addTo(free)
            } else if (status.startsWith("unfree")) {
                layer.addTo(unfree)
            } else {
                layer.addTo(unmarked)
            }

            if (feature.properties.Year <= 1599) {
                layer.addTo(c16);
            } else if ((feature.properties.Year >= 1600) && (feature.properties.Year <= 1699)) {
                layer.addTo(c17);
            } else if ((feature.properties.Year >= 1700) && (feature.properties.Year <= 1799)) {
                layer.addTo(c18);
            } else if ((feature.properties.Year >= 1800) && (feature.properties.Year <= 1900)) {
                layer.addTo(c19);
            } else { layer.addTo(undated) }
        }

    });
// IDK why `clustermouseover` actually triggers on a click and `clusterclick` triggers on the *second* click of a cluster
// popup shows a cluster's location, taken from the first record in the cluster, and how many records it holds
mcg.on('clustermouseover', function(a) {
    var clusterCount = a.layer.getChildCount();
    var clusterChildren = a.layer.getAllChildMarkers();
    var clusterLocation = [];

    let i;
    for (i = 0; i < clusterCount; i++) {
        clusterLocation.push(clusterChildren[i].feature.properties.from);
        var clusterName = clusterLocation.shift();
    };

    var clusterPopup = clusterName + '<br />' + clusterCount + ' people are in the database in this location.';
    a.layer.bindPopup(clusterPopup);
});
let basemapsControl = L.control.layers(basemaps, null, { collapsed: false }).addTo(map);
let freedomControls = L.control.layers(null, null, { collapsed: false, position: "bottomleft" });
let datesControls = L.control.layers(null, null, { collapsed: false, position: "bottomleft" });
freedomControls.addOverlay(unmarked, 'records with weird freedom status').addOverlay(free, 'Free').addOverlay(unfree, 'Unfree').addTo(map);
datesControls.addOverlay(c16, '1492 - 1599').addOverlay(c17, '1600 - 1699').addOverlay(c18, '1700 - 1799').addOverlay(c19, '1800 - 1900').addTo(map);
// move the two overlay controls outside the map for styling etc
// get the parents of the controls, add ids to specify which is which
let oldfreedomParent = freedomControls.getContainer();
    oldfreedomParent.setAttribute("id", "freedomControls");
let olddatesParent = datesControls.getContainer();
    olddatesParent.setAttribute("id", "datesControls");
let newfreedomParent = document.getElementById('freedom-controls');
let newdatesParent = document.getElementById('dates-controls');

    newfreedomParent.appendChild(document.getElementById('freedomControls'));
    newdatesParent.appendChild(document.getElementById('datesControls'));
