'use strict';
{
    const $ = django.jQuery;

    $(function() {
        $('#id_category').on('change', function() {
            if ($(this).val()) {
                $('#id_alias').val(null).trigger('change');
            }
        });
    });
}
