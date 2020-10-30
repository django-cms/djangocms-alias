import $ from 'jquery';
import { initActions } from './actions';
import { initSortable } from './sortable';
import { initCollapse } from './collapse';
import { initSiteFilter } from './siteFilter';

$(() => {
    initActions();
    initSortable();
    initCollapse();
    initSiteFilter();
});
