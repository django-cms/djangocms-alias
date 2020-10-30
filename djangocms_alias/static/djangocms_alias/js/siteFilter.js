import $ from 'jquery';

export function initSiteFilter() {
    const $siteSelector = $('#sitefilter');
    const url_string = window.location.href
    let url = new URL(url_string);
    const id = url.searchParams.get("site") != null ? url.searchParams.get("site") : '';

    // On load we may need to preset a site
    $siteSelector.val(id)

    $siteSelector.on('change', function(){
        const endpoint = window.location.pathname;
        const id = $(this).val();

        url.searchParams.set("site", id)
        window.location.href = url;
    });
}
