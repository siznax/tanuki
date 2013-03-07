// siznax 2013

$( function() {

    $( "a.load_video" ).click( function( event ) {
	$( "#viewtube" ).html('<iframe width="420" height="315" src="http://www.youtube.com/embed/' + event.target.id + '" frameborder="0" allowfullscreen></iframe>');
	return false;
    });

    $( ".entry.video.stream .entry_body" ).click( function() {
	var html = event.target.innerHTML;
	var href = html.match(/href="([^\"]*)"/)[1];
	event.target.innerHTML = '<iframe src="' + href + '"></iframe>';
	console.log( event.target );
    });


});
