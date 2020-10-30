$(document).ready(function(){
    $("#sitefilter").on('change', function(){
       var endpoint = window.location.pathname;
       var id = $(this).val() ;
       var url = id!='all' ? endpoint +"?site="+id : endpoint;
       window.location.href = url;

    });
})
$(window).load(function(){
    var url_string = window.location.href
    var url = new URL(url_string);
    var id = url.searchParams.get("site") != null ? url.searchParams.get("site") : 'all';
    $('#sitefilter').val(id)
})
