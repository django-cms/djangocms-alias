'use strict';
{
    const $ = django.jQuery;
    const itemsPerPage = 30;

    function ajaxConfig(endpoint, extraData) {
        return {
            url: endpoint,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                const data = {
                    term: params.term || '',
                    page: params.page || 1,
                    limit: itemsPerPage,
                };
                if (extraData) {
                    Object.assign(data, extraData());
                }
                return data;
            },
            processResults: function(data) {
                return {
                    results: data.results,
                    pagination: { more: data.more },
                };
            },
        };
    }

    $(function() {
        const $siteField = $('#id_site');
        const $categoryField = $('#id_category');
        const $aliasField = $('#id_alias');

        $categoryField.select2({
            allowClear: true,
            ajax: ajaxConfig($categoryField.attr('data-select2-url'), function() {
                return { site: $siteField.val() };
            }),
        });

        $aliasField.select2({
            ajax: ajaxConfig($aliasField.attr('data-select2-url'), function() {
                return {
                    site: $siteField.val(),
                    category: $categoryField.val(),
                };
            }),
        });
    });
}
