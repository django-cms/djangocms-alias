import $ from 'jquery';

$(function() {
    var itemsPerPage = 30;
    var siteField = $('#id_site');
    var categoryField = $('#id_category');
    var aliasField = $('#id_alias');
    var categoryEndpoint = categoryField.attr('data-select2-url');
    var aliasEndpoint = aliasField.attr('data-select2-url');

    categoryField.select2({
        allowClear: true,
        ajax: {
            url: categoryEndpoint,
            dataType: 'json',
            quietMillis: 250,
            data: function(term, page) {
                return {
                    term: term,
                    page: page,
                    limit: itemsPerPage,
                    site: siteField.val(),
                };
            },
            results: function(data) {
                return data;
            }
        },
        initSelection: function(element, callback) {
            var categoryId = element.val();

            $.ajax({
                url: categoryEndpoint,
                dataType: 'json',
                data: {
                    pk: categoryId
                }
            }).done(function(data) {
                var text = categoryId;

                if (data.results.length) {
                    text = data.results[0].text;
                }
                callback({ id: categoryId, text: text });
            }).fail(function() {
                callback({ id: categoryId, text: categoryId });
            });
        }
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
                    site: siteField.val(),
                    category: categoryField.val()
                };
            },
            results: function(data) {
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
