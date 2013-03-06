// siznax 2013

$( function() {

    $( "a.load_video" ).click( function( event ) {
	$( "#viewtube" ).html('<iframe width="420" height="315" src="http://www.youtube.com/embed/' + event.target.id + '" frameborder="0" allowfullscreen></iframe>');
	return false;
    });

});
