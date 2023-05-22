/* If the category field is changed the alias field's value is reset.
 */

$(document).ready(function() {
    // Category field change event
    $('#id_category').change(function(){
        let categoryValue = $('#id_alias').select2('val');
        // if category is set, remove the value from alias (which might be of another category)
        if (categoryValue) {
            $('#id_alias').select2('val', '');
        }
    });
});
