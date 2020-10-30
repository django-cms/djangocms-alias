import $ from 'jquery';

export function initSiteFilter() {
    const $siteSelector = $('#sitefilter');
    const url_string = window.location.href
    let url = new URL(url_string);
    const loadedSiteId = url.searchParams.get("site") != null ? url.searchParams.get("site") : '';

    // On load we may need to preset a site
    $siteSelector.val(loadedSiteId)

    $siteSelector.on('change', function() {
        const endpoint = window.location.pathname;
        const changedSiteId = $(this).val();

        // Remove the get param if nothing is set
        if (changedSiteId == "") {
            url.searchParams.delete("site")
        }
        // Change the get param if the value is set
        else {
            url.searchParams.set("site", changedSiteId)
        }
        // Force a window reload with the new value set to trigger a rerender
        window.location.href = url;
    });
}
