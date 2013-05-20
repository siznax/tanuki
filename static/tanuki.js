// siznax 2013

$( function() {

    // Leaflet JS maps -----------------------------------------

    if ( $(".leafletjs").length ) {
	var map  = $( "div.leafletjs" ).attr("id");
	var lat  = $( "div.leafletjs" ).attr("lat");
	var lon  = $( "div.leafletjs" ).attr("lon");
	var zoom = $( "div.leafletjs" ).attr("zoom");
	// alert("found map: " + map + " [" + lat + "," + lon + "] " + zoom );
	map = L.map( map ).setView( [lat,lon],zoom );
	var API_KEY = $( "#leafletjs_api_key" ).attr("key");
	L.tileLayer('http://{s}.tile.cloudmade.com/'+API_KEY+'/997/256/{z}/{x}/{y}.png', { attribution:'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>', maxZoom:18 }).addTo( map );
    }

    // Youtube playlist ----------------------------------------

    if ( $("#playlist").length ) {
	// alert("found playlist");
	if ( $("#viewtube").length==0 ) {
	    $( "#playlist" ).prepend("<div id=\"viewtube\"></div>");
	}
	changeChannel( $("#playlist a")[0].id );
    }

    $( "#playlist a" ).click( function( event ) {
	changeChannel( event.target.id );
	return false;
    });

    function changeChannel( id ) {
	$( "#viewtube" ).html('<iframe width="420" height="315"'
			      + ' src="http://www.youtube.com/embed/'
			      + id + '" frameborder="0" allowfullscreen>'
			      + '</iframe>');
    }

});
