// gallery.js (coupled w/gallery.css) siznax 2013

$( function() {

    var DEBUG = true;
    var g = new Object();

    // find galleries
    if ( $(".galleryjs img").length ) {
	$( ".galleryjs" ).each( function() {
	    var gid = $( this ).closest("div[id]").attr("id");
	    var num = $( "#" + gid + " img").length;
	    g[gid] = new Object();
	    g[gid]['num'] = num;
	    if ( ! g.hasOwnProperty('id') ) { // set id to first found
		g['id'] = gid;
	    }
	    console.log( "TANUKI found gallery #" + gid + " num=" + num );
	});
	console.log( g );
    }

    // click gallery img
    $( ".galleryjs img" ).click( function() {
	var gid = $( this ).closest("div[id]").attr("id");
	g['id'] = gid;
	var src = event.target.src;
	var i = getIndex( src );
	console.log("+ clicked gallery #"+gid+" img["+i+"] "+src);
	putSlide( src );
    });

    // click slide img
    $( "body" ).on( "click", "#slide img", function() {
	var src = event.target.src;
	var gid = g['id'];
	var i = getIndex( src );
	if ( DEBUG ) {
	    console.log("+ clicked slide img #" + gid + "[" + i+ "] " + src );
	}
	nextSlide( gid,i );
    });

    // click slide (but not img)
    $("body").on( "click", "#slide", function() {
	if ( event.target.id=="slide" ) {
	    removeSlide();
	}
    });

    $( document ).keyup( function(e) {
	// console.log( "pressed key "+ e.keyCode );
	if (e.keyCode==27) { // pressed ESC
	    removeSlide(); 
	}
	if (e.keyCode==74) { // pressed j (NEXT)
	    if ( $("#slide").length ) {
		nextSlide( g['id'],getIndex($("#slide img")[0].src) ); 
	    } else {
		nextSlide( g['id'],-1 );
	    }
	}
	if (e.keyCode==75) { // pressed k (PREV)
	    if ( $("#slide").length ) {
		prevSlide( g['id'],getIndex($("#slide img")[0].src) ); 
	    } else {
		last = g[g['id']]['num'];
		prevSlide( g['id'],last );
	    }
	}
	if (e.keyCode==83) { // pressed s (SIZE)
	    if ( $("#slide img").length ) {
		sizeImg();
	    }
	}
    });

    function initSlide() {
	if ( $("#slide").length == 0 ) {
    	    $("body").append("<div id=slide><img></div>");
    	    $("#slide img").bind( "load", slowSizeImg ); // may fire X times
    	    if ( DEBUG ) { 
    		console.log( "+ append/bind #slide img");
    	    }
	}
    }

    function setAspect( iw,ih ) {
	g['aspect'] = "WIDE";
	if ( ih > iw ) {
	    g['aspect'] = "TALL";
	}
    }

    function slowSizeImg() {
	window.setTimeout( sizeImg, 100 );
	window.setTimeout( setMarginTop, 150 );
    }

    function sizeImg() {
	if ( $("#slide").length==0 ) {
	    return false;
	}
	var sw = $("#slide").width();
	var sh = $("#slide").height();
	var iw = $("#slide img")[0].naturalWidth;
	var ih = $("#slide img")[0].naturalHeight;
	console.log( "+ sizeImg slide " + sw+"x"+sh + " img " + iw+"x"+ih );
	setAspect( iw,ih );
	if ( (iw>sw) && (ih>sh) ) { tallView(); }
	else if ( iw > sw ) { wideView(sh); }
	else if ( ih > sh ) { tallView(sh); }
	else { unscaled(); }
	if ( DEBUG ) {
	    var scaled = $("#slide img").width() 
		+ "x" + $("#slide img").height();
	    var natural = $("#slide img")[0].naturalWidth 
		+ "x" + $("#slide img")[0].naturalHeight;
	    console.log( "  img scaled " + scaled + " natural " + natural );
        }
    }

    function wideView( sh ) {
	if ( DEBUG ) {
	    console.log("  aspect " + g['aspect'] + " view WIDE");
	}
	$( "#slide img" ).css("width","100%");
	$( "#slide img" ).css("height","auto");
    }

    function tallView() {
	if ( DEBUG ) {
	    console.log("  aspect " + g['aspect'] + " view TALL");
	}
	$( "#slide img" ).css("width","auto");
	$( "#slide img" ).css("height","100%");
	$( "#slide img" ).css( "margin-top",0 );
    }

    function unscaled() {
	if ( DEBUG ) {
	    console.log("  aspect " + g['aspect'] + " view UNSCALED");
	}
	var sh = $("#slide").height();
	var ih = $("#slide img").height();
    }

    function setMarginTop() {
	var slide_height = $("#slide").height();
	var image_height = $("#slide img").height();
	var top = Math.floor( (slide_height - image_height)/2 );
	if (DEBUG) {
	    console.log( "  setMarginTop sh=" + slide_height + " ih=" + image_height );
	}
	$( "#slide img" ).css( "margin-top",top );
    }

    function putSlide( src ) {
	if ( DEBUG ) {
	    console.log( "+ putSlide #" + g['id'] + "[" + getIndex( src ) + "] " + src );
	}
	initSlide();
	$("#slide img").attr("src",src);
	$("#slide img").css("width","auto");
	$("#slide img").css("height","auto");
	$("#slide").css( "top",$("body").scrollTop() );
	$("#slide").css("display","block");
	$("body").css("overflow","hidden");
    }

    function getIndex( src ) {
	if ( ( ! src ) || ( ! g['id'] ) ) { 
	    alert("tanuki gallery.js IndexError");
	}
	var found = 0;
	$("#" + g['id'] + " img").each( function(i) {
	    if (this.src==src) {  
		found=i; 
	    }
	});
	return found;
    }

    function nextSlide( gid,i ) {
	var next = i+1;
	if ( DEBUG ) {
	    console.log( "+ nextSlide #" + gid + " " + i + "=>" + next );
	}
	if ( next > g[gid]['num']-1 ) {
	    removeSlide();
	    return false;
	}
	putSlide( $("#"+gid+" img")[next].src );
    }

    function prevSlide( gid,i ) {
	var prev = i-1;
	if ( DEBUG ) {
	    console.log( "+ prevSlide #" + gid + " " + i + "=>" + prev );
	}
	if ( prev < 0 ) {
	    removeSlide();
	    return false;
	}
	putSlide( $("#"+gid+" img")[prev].src );
    }

    function removeSlide() {
	$("#slide img").off();
	$( "#slide" ).remove();
	$( "body" ).css( "overflow","auto" );
	if ( DEBUG ) {
	    console.log( "+ removed #slide" );
	}
    }

});
