// gallery.js (coupled w/gallery.css) siznax 2013

$( function() {

    var DEBUG = false;

    if ( $(".galleryjs img").length ) {
	$( ".galleryjs" ).each( function() {
	    var gid = $( this ).closest("div[id]").attr("id");
	    var num = $( "#" + gid + " img").length;
	    console.log( "TANUKI found gallery #" + gid + " num=" + num );
	    initSlide( gid,num );
	});
    }

    function initSlide( gid, num ) {
	if ( $("#slide").length == 0 ) {
    	    if ( DEBUG ) { 
    		console.log( "+ append #slide gid=" + gid + " num=" + num );
    	    }
    	    $("body").append("<div id=slide><img></div>");
    	    $("#slide img").bind( "load", sizeSlide );
	}
    }

    $( ".galleryjs img" ).click( function() {
	var gid = $( event.target ).closest("div[id]").attr("id");
	var num = $("#" + gid + " img").length;
	initSlide( gid, num );
    	$("#slide").attr( "gid",gid );
    	$("#slide").attr( "num",num );
	putSlide( event.target.src );
    });

    function sizeSlide() {
	var width = $("#slide img").width();
	var height = $("#slide img").height();
	var aspect = null;
	if ( width > height ) {
	    aspect = "WIDE";
	} else {
	    aspect = "TALL";
	}
	slideReport();
	if ( aspect=='WIDE' ) {
	    if ( width > $("#slide").width() ) {
	    	wideView( aspect );
	    } else {
		unscaledView( aspect );
	    }
	} else if ( aspect=='TALL' ) {
	    if ( height > $("#slide").height() ) {
	    	tallView( aspect );
	    } else {
		unscaledView( aspect );
	    }
	} else {
	    unscaledView( aspect );
	}
	if ( DEBUG ) {
	    var width = $("#slide img").width();
	    var height = $("#slide img").height();
	    console.log( "+ img loaded " + width + "x" + height );
        }
    }

    function slideReport() {
       var width = $("#slide img").width();
       var height = $("#slide img").height();
       var slide_height = $("#slide").height();
       var slide_width = $("#slide").width();
       if ( DEBUG ) {
	   sdim = "slide " + slide_height + "x" + slide_width;
	   idim = "img " + width + "x" + height;
	   console.log( "> " + sdim + " " + idim );
       }
    }

    function wideView( aspect ) {
       if ( DEBUG ) {
	   console.log("> aspect " + aspect + " view WIDE");
       }
       var slide_height = $("#slide").height();
       $( "#slide img" ).css("width","100%");
       $( "#slide img" ).css("height","auto");
       var scaled_height = $("#slide img").height()
       var margin_top = Math.floor( (slide_height-scaled_height)/2 );
       $( "#slide img" ).css( "margin-top",margin_top );
   }

   function tallView( aspect ) {
       if ( DEBUG ) {
	   console.log("> aspect " + aspect + " view TALL");
       }
       $( "#slide img" ).css("width","auto");
       $( "#slide img" ).css("height","100%");
       $( "#slide img" ).css( "margin-top",0 );
    }

    function unscaledView( aspect ) {
	if ( DEBUG ) {
	    console.log("> aspect " + aspect + " view NOSCALE");
	}
	var img_height = $("#slide img").height();
	var slide_height = $("#slide").height();
	var margin_top = Math.floor( (slide_height-img_height)/2 );
	$( "#slide img" ).css( "margin-top",margin_top );
    }

    $( "body" ).on( "click", "#slide img", function() {
	var gid = $("#slide").attr("gid");
	var src = event.target.src
	nextSlide( gid,src );
    });

    $("body").on( "click", "#slide", function() {
	if ( event.target.id=="slide" ) {
	    $("#slide img").off();
	    removeSlide();
	}
    });

    function putSlide( src, index ) {
	if ( DEBUG ) {
	    console.log("+ put slide[" + index + "] " + src );
	}
	$("#slide img").attr("src",src);
	$("#slide img").css("width","auto");
	$("#slide img").css("height","auto");
	$("#slide").css( "top",$("body").scrollTop() );
	$("#slide").css("display","block");
	$("body").css("overflow","hidden");
    }

    function nextSlide( gid, src ) {
	var next = 0;
	var last = $("#slide").attr("num") - 1;
	$("#" + gid + " img").each( function(i) {
	    if (this.src==src) {
		clicked = i;
		next = i + 1;
	    }
	});
	if ( DEBUG ) {
	    console.log( "> #" + gid + " clicked " + clicked + " next " + next );
	}
	if ( next > last ) {
	    removeSlide();
	    return false;
	} 
	var next_image = $("#" + gid + " img")[next].src;
	if ( DEBUG ) {
	    console.log( "+ #" + gid + " next image[" + next + "] " + next_image );
	}
	putSlide( next_image, next );
    }

    function removeSlide() {
	$( "#slide" ).remove();
	$( "body" ).css( "overflow","auto" );
	if ( DEBUG ) {
	    console.log( "+ #slide removed" );
	}
    }

});
