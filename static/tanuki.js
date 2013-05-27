// siznax 2013

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

    // IMAGE GALLERY -------------------------------------------

    if ( $(".gallery img").length ) {
	var id = $( ".gallery" ).closest("div[id]").attr("id");
	var num = $(".gallery img").length;
	console.log( "TANUKI found gallery id=" + id + " (" + num + ")" );
    }

    $( ".gallery img" ).click( function() {
	if ( $("#slide").length == 0 ) {
	    if ( DEBUG ) { 
		console.log( "+ append #slide");
	    }
	    $("body").append("<div id=slide><img></div>");
	    $("#slide img").bind( "load", sizeSlide );
	    $("#slide").attr( "num", $(".gallery img").length );
	    putSlide( event.target.src );
	}
    });

    function sizeSlide() {
	var wide = "tall";
	$("#slide img").css("width","auto");
	$("#slide img").css("height","100%");
	var width = $("#slide img").width();
	var height = $("#slide img").height();
	if ( DEBUG ) {
	    console.log( "> slide loaded " + width + "x" + height );
	}
	if ( width > height ) {
	    wide = "wide";
	}
	if ( width > $("body").width() ) {
	    if ( DEBUG ) {
		console.log("> wide view");
	    }
	    $( "#slide img" ).css("width","100%");
	    $( "#slide img" ).css("height","auto");
	    $( "#slide img" ).css("margin-top",Math.floor(($("#slide").height() - $("#slide img").height())/2));
	} else {
	    $( "#slide img" ).css("width","auto");
	    $( "#slide img" ).css("height","100%");
	    $( "#slide img" ).css("margin-top",0);
	}
	if ( DEBUG ) {
	    console.log( "+ slide loaded " + width + "x" + height + " " + wide );
	}
    }

    $( "body" ).on( "click", "#slide img", function() {
	nextSlide( event.target.src );
    });

    $("body").on( "click", "#slide", function() {
	if ( event.target.id=="slide" ) {
	    $("#slide img").off();
	    removeSlide();
	}
    });

    function putSlide( src ) {
	if ( DEBUG ) {
	    console.log("+ put slide " + src);
	}
	var width = $("body").width();
	var height = $("body").height();
	$("#slide img").attr("src",src);
	$("#slide").css( "top",$("body").scrollTop() );
	$("#slide").css("display","block");
	$("body").css("overflow","hidden");
    }

    function nextSlide( src ) {
	var next = 0;
	var last = $("#slide").attr("num") - 1;
	$(".gallery img").each( function(i) {
	    if (this.src==event.target.src) {
		clicked = i;
		next = i + 1;
	    }
	});
	if ( next > last ) {
	    removeSlide();
	    return false;
	} 
	var next_image = $(".gallery img")[next].src;
	if ( DEBUG ) {
	    console.log( "+ next " + clicked + ":" + next + " " + next_image );
	}
	putSlide( next_image );
    }

    function removeSlide() {
	$( "#slide" ).remove();
	$( "body" ).css( "overflow","auto" );
	if ( DEBUG ) {
	    console.log( "+ #slide removed" );
	}
    }

});
