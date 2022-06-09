// The current site is preselected for the user in the Site field
// Once the site is selected with a value the Category field becomes active
// In the Category field, the list of available categories is updated based on the selected Site
// Once the Category field is selected, the Alias field becomes active
// In the Alias field, the list of available aliases is updated based on the selected Category (Existing)
// If the Site field is updated, the Category field will be reset and Alias field inactive until the Category selection is made
// If the user Saves without selecting an Alias, an error message will be displayed and the Plugin will not save. (Existing)
// The Save CTA will remain active at all time. (Existing)

function disableAlias(param){
    $('#id_alias').prop( "disabled", param );
}

function disableCategory(param){
    $('#id_category').prop( "disabled", param );
}

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
                disableAlias(true)
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
        console.log(spanText)
        if (spanText != "Select category to restrict the list of aliases below") {
            disableAlias(false)
        }
        // in case the category field is cleared, we need to disable the alias field again
        else{
             disableAlias(true)
        }
    });
})

// Site field change event
$(document).ready(function() {
    $('#id_site').change(function(){
        // If the site changes, category should be reset
        let catSpanTag = $("#s2id_id_category > a > span")
        catSpanTag[0].childNodes[0].textContent = "Select category to restrict the list of aliases below"
        disableAlias(true)

        var siteName = $('#id_site').find(":selected").text();
        // If the site is changed to none, alias should be disabled
        if(siteName == "---------"){
            disableAlias(true)
            disableCategory(true)
        }
        else{
            disableCategory(false)
        }
    });
})
