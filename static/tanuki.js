// tanuki.js siznax 2013

$( function() {

    var DEBUG = false;

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
