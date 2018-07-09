import $ from 'jquery';

export function initCollapse() {
    var collapsedClass = 'cms-alias-sortable-collapsed';
    var expandedClass = 'cms-alias-sortable-expanded';

    // Custom collapsing/extending
    $('.cms-alias-sortable-show-hide-button').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const $btn = $(this);
        const $listItem = $btn.closest('.cms-aliases-list-item');

        if ($listItem.hasClass(collapsedClass)) {
            $listItem.removeClass(collapsedClass).addClass(expandedClass);
        } else {
            $listItem.removeClass(expandedClass).addClass(collapsedClass);
        }
    });
}
