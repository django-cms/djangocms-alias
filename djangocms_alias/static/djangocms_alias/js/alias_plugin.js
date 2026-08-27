'use strict';
{
    const $ = django.jQuery;

    /**
     * Same as `admin/js/autocomplete.js`, but the request also carries the site
     * and the category currently selected in the alias plugin form so that the
     * admin autocomplete endpoint can narrow the results down.
     */
    $.fn.djangocmsAliasSelect2 = function() {
        $.each(this, function(i, element) {
            $(element).select2({
                ajax: {
                    data: (params) => {
                        const data = {
                            term: params.term,
                            page: params.page,
                            app_label: element.dataset.appLabel,
                            model_name: element.dataset.modelName,
                            field_name: element.dataset.fieldName
                        };
                        const site = $('#id_site').val();
                        const category = $('#id_category').val();

                        if (site) {
                            data.site = site;
                        }
                        if (category && element.id !== 'id_category') {
                            data.category = category;
                        }
                        return data;
                    }
                }
            });
        });
        return this;
    };

    $(function() {
        $('.djangocms-alias-autocomplete').not('[name*=__prefix__]').djangocmsAliasSelect2();

        $('#id_category').on('change', function() {
            if ($(this).val()) {
                // The alias choices depend on the category - drop a selection
                // that may no longer be part of them.
                $('#id_alias').val(null).trigger('change');
            }
        });
    });
}
