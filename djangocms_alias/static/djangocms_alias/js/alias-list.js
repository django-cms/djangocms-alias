(function($) {
    $(document).ready(function() {
        var $sortableRoot = $('.cms-aliases-sortable');

        $sortableRoot.nestedSortable({
            forcePlaceholderSize: true,
            items: '.cms-aliases-list-item',
            handle: 'div.cms-alias-draggable',
            maxLevels: 1,
            opacity: 0.6,
            update: function(evt, object) {
                // cancel request if already in progress
                if (window.CMS.API.locked) {
                    return false;
                }
                window.CMS.API.locked = true;

                var ajaxUrl = $sortableRoot.data('ajaxUrl');
                var $item = object.item;
                var aliasId = $item.data('aliasId');
                var position = $item.index();

                $.ajax({
                    method: 'POST',
                    url: ajaxUrl,
                    data: {
                        alias_id: aliasId,
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
                        var msg = window.CMS.config.lang.error;
                        window.CMS.API.Messages.open({
                            message: msg + jqXHR.responseText || jqXHR.status + ' ' + jqXHR.statusText,
                            error: true
                        });
                    }
                });
            }
        });

        var collapsedClass = 'cms-alias-sortable-collapsed';
        var expandedClass = 'cms-alias-sortable-expanded';
        var showText = $sortableRoot.data('showText');
        var hideText = $sortableRoot.data('hideText');

        // start collapsed
        $sortableRoot.find('> .cms-aliases-list-item').each(function() {
            $(this).addClass(collapsedClass);
        });

        // Custom collapsing/extending
        $('.cms-alias-sortable-show-hide-button').on('click', function(evt) {
            $btn = $(this);
            $listItem = $btn.parents('.cms-aliases-list-item');

            if ($listItem.hasClass(collapsedClass)) {
                $listItem.removeClass(collapsedClass).addClass(expandedClass);
                $btn.html(hideText);
            } else {
                $listItem.removeClass(expandedClass).addClass(collapsedClass);
                $btn.html(showText);
            }
        });
    });
})(CMS.$);
