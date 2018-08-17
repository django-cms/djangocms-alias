import $ from 'jquery';

export function initActions() {
    $('.cms-alias-btn').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        CMS.API.Toolbar._delegate($(this));
    });
}
