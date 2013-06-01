// tanuki.js siznax 2013

$( function() {

    var DEBUG = false;

    // Leaflet JS maps -----------------------------------------

    if ( $(".leafletjs").length ) {
	var map  = $( "div.leafletjs" ).attr("id");
	var lat  = $( "div.leafletjs" ).attr("lat");
	var lon  = $( "div.leafletjs" ).attr("lon");
	var zoom = $( "div.leafletjs" ).attr("zoom");
	console.log("TANUKI found map: " + map + " [" + lat + "," + lon + "] " + zoom );
	map = L.map( map ).setView( [lat,lon],zoom );
	var API_KEY = $( "#leafletjs_api_key" ).attr("key");
	L.tileLayer('http://{s}.tile.cloudmade.com/'+API_KEY+'/997/256/{z}/{x}/{y}.png', { attribution:'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>', maxZoom:18 }).addTo( map );
    }

    // Youtube playlist ----------------------------------------

    $("div.playlist").each( function() {
	playlist = $(this).attr("id");
	console.log( "TANUKI found playlist: " + playlist );
	// setup one viewtube only
	if ( $( "#viewtube" ).length==0 ) {
	    $( "#"+playlist ).prepend("<div id=\"viewtube\"></div>");
	    first_video = $( "#"+playlist+" a" ).attr("id");
	    changeChannel( first_video );
	}
    });

    $( ".playlist a" ).click( function( event ) {
	highlightClicked( event.target.id );
	changeChannel( event.target.id );
	return false;
    });

    function changeChannel( video ) {
	console.log( "changeChannel(" + video + ")");
	$( "#viewtube" ).html('<iframe width="420" height="315"'
			      + ' src="http://www.youtube.com/embed/'
			      + video + '" frameborder="0" allowfullscreen>'
			      + '</iframe>');
    }

    function highlightClicked( id ) {
	console.log( "highlightClicked " + id );
	var last = $( "#viewtube" ).attr( "last" );
	$( "#"+last ).css( "font-weight", "normal");
	$( "#"+last ).closest( "li" )
	    .css( "list-style-type", "disc" );
	$( "#viewtube" ).attr( "last", id );
	$( "#"+id ).css( "font-weight", "bold" );
	$( "#"+id ).closest( "li" )
	    .css( "list-style-type", "circle" );
    }

});
