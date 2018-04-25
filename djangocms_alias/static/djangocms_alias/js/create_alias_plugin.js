(function($) {
    $(function() {
        var itemsPerPage = 30;
        var categoryField = $('#id_category');
        var aliasField = $('#id_alias');
        var aliasEndpoint = aliasField.attr('data-select2-url');
        categoryField.select2({
            allowClear: true
        });
        aliasField.select2({
            ajax: {
                url: aliasEndpoint,
                dataType: 'json',
                quietMillis: 250,
                data: function(term, page) {
                    return {
                        term: term,
                        page: page,
                        limit: itemsPerPage,
                        category: categoryField.val()
                    };
                },
                results: function(data, page) {
                    return data;
                }
            },
            initSelection: function(element, callback) {
                var aliasId = element.val();
                $.ajax({
                    url: aliasEndpoint,
                    dataType: 'json',
                    data: {
                        pk: aliasId
                    }
                })
                    .done(function(data) {
                        var text = aliasId;
                        if (data.results.length) {
                            text = data.results[0].text;
                        }
                        callback({ id: aliasId, text: text });
                    })
                    .fail(function() {
                        callback({ id: aliasId, text: aliasId });
                    });
            }
        });
    });
})(CMS.$);
