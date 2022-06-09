// The current site is preselected for the user in the Site field
// Once the site is selected with a value the Category field becomes active
// In the Category field, the list of available categories is updated based on the selected Site
// Once the Category field is selected, the Alias field becomes active
// In the Alias field, the list of available aliases is updated based on the selected Category
// If the Site field is updated, the Category field will be reset and Alias field inactive until the Category selection is made

const aliasDropdownFirst = "Select an alias";
const categoryDropdownFirst = "Select category to restrict the list of aliases below";
const siteDropDownFirst = "---------";

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
        let aliasSpanTag = $("#s2id_id_alias > a > span");
        let aliasSpanText = aliasSpanTag[0].childNodes[0].textContent;
        if (aliasSpanText == aliasDropdownFirst){
            // This means alias is not set so lets check category
            let catSpanTag = $("#s2id_id_category > a > span");
            let catSpanText = catSpanTag[0].childNodes[0].textContent;
            if (catSpanText == categoryDropdownFirst) {
                // Category is not set so let's disable alias
                disableAlias(true);
            }
        }
    }
});

// Category field change event
$(document).ready(function() {
    $('#id_category').change(function(){
        let catSpanTag = $("#s2id_id_category > a > span")
        let catSpanText = catSpanTag[0].childNodes[0].textContent
        // if category is set, remove the disable attribute
        if (catSpanText != categoryDropdownFirst) {
            disableAlias(false)
        }
        // In case the category field is cleared, we need to disable the alias field again
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
        catSpanTag[0].childNodes[0].textContent = categoryDropdownFirst
        disableAlias(true)

        let siteName = $('#id_site').find(":selected").text();
        // If the site is changed to none, alias should be disabled
        if(siteName == siteDropDownFirst){
            disableAlias(true)
            disableCategory(true)
        }
        else{
            disableCategory(false)
        }
    });
})
