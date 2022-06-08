
// Onload we check if alias is set, if it is, we do nothing
// if alias is not set, we check if category is set, if category is not set,
// the alias field is disabled until populated
$(document).ready(function() {
    let catDiv = $('.field-category');
    if (catDiv.length){
        let aliasSpanTag = $("#s2id_id_alias > a > span")
        let aliasSpanText = aliasSpanTag[0].childNodes[0].textContent
        if (aliasSpanText == "Select an alias"){
            // This means alias is not set so lets check category
            let catSpanTag = $("#s2id_id_category > a > span")
            let spanText = catSpanTag[0].childNodes[0].textContent
            if (spanText == "Select category to restrict the list of aliases below") {
                // Category is not set so let's disable alias
                $('#id_alias').prop( "disabled", true );
            }
        }
    }
});

// Category field change event
$(document).ready(function() {
    $('#id_category').change(function(){
        let catSpanTag = $("#s2id_id_category > a > span")
        let spanText = catSpanTag[0].childNodes[0].textContent
        // if category is set, remove the disable attribute
        if (spanText != "Select category to restrict the list of aliases below") {
            $('#id_alias').prop( "disabled", false );
        }
        // in case the category field is cleared, we need to disable the alias field again
        else{
             $('#id_alias').prop( "disabled", true );
        }
    });
})


// Site field change event
$(document).ready(function() {
    $('#id_site').change(function(){
        var siteName = $('#id_site').find(":selected").text();
        // If the site is changed to none, alias should be disabled
        if(siteName == "---------"){
            $('#id_alias').prop( "disabled", true );
        }
        else{
            $('#id_alias').prop( "disabled", false );
        }
    });
})


