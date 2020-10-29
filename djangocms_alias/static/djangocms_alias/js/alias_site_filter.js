
$(document).ready(function(){
    $("#sitefilter").on('change', function(){
       var endpoint = window.location.pathname;
       var id = $(this).val();
       var url = id>0 ? endpoint +"?site="+id : endpoint;
       window.location.href = url;
    });
})
