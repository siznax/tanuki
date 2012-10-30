// window.onload = function(){ alert("okay"); }

function swapColorCSS( sheet ) { 
    href = '/static/' + sheet;
    document.getElementById( 'color' ).setAttribute( 'href', href );
}

function validate() {
    date = document.getElementById('date_box');
    if (date.value.length !== 10 || 
	date.value.match("\\d{4}-\\d{2}-\\d{2}")==null) {
	alert("Warning! Malformed date.");
	date.focus();
	return false;
    } else { 
	return true;
    }
}

$(document).ready(function(){
    
    // $("body").css("border","3px solid orange");

});
