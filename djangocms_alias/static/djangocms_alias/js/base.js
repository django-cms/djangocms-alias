import $ from 'jquery';
import { initActions } from './actions';
import { initSortable } from './sortable';
import { initCollapse } from './collapse';

$(() => {
    initActions();
    initSortable();
    initCollapse();
});
