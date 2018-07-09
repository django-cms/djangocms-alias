import $ from 'jquery';
import { initSortable } from './sortable';
import { initCollapse } from './collapse';

$(() => {
    initSortable();
    initCollapse();
});
