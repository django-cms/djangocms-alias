import $ from 'jquery';

export function initActions() {
    $('.cms-alias-btn').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        debugger;
        // CMS.Toolbar._delegate($(this));
    });
}
