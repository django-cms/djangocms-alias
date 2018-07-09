import $ from 'jquery';

export function initSortable() {
    var $sortableRoot = $('.cms-aliases-sortable');

    $sortableRoot.nestedSortable({
        forcePlaceholderSize: true,
        items: '.cms-aliases-list-item',
        listType: 'div',
        handle: 'div.cms-alias-draggable',
        maxLevels: 1,
        opacity: 0.6,
        cursor: 'move',
        delay: 10,
        update: function(evt, object) {
            // cancel request if already in progress
            if (window.CMS.API.locked) {
                return false;
            }
            window.CMS.API.locked = true;

            const $item = object.item;
            const position = $item.index();
            const { ajaxUrl, aliasId } = $sortableRoot.data();

            $.ajax({
                method: 'POST',
                url: ajaxUrl,
                data: {
                    alias: aliasId,
                    position: position,
                    csrfmiddlewaretoken: window.CMS.config.csrf
                },
                success: function() {
                    // enable actions again
                    window.CMS.API.locked = false;
                },
                error: function(jqXHR) {
                    window.CMS.API.locked = false;

                    // revert position because of error
                    $sortableRoot.sortable('cancel');

                    // trigger error
                    const msg = window.CMS.config.lang.error;

                    window.CMS.API.Messages.open({
                        message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                        error: true
                    });
                }
            });
        }
    });
}
