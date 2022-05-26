// #####################################################################################################################
// #IMPORTS#
const gulp = require('gulp');
const gutil = require('gulp-util');
const webpack = require('webpack');

var argv = require('minimist')(process.argv.slice(2)); // eslint-disable-line

// #####################################################################################################################
// #SETTINGS#
var options = {
    debug: argv.debug,
};
var PROJECT_ROOT = __dirname + '/djangocms_alias/static/djangocms_alias';
var PROJECT_PATH = {
    js: PROJECT_ROOT + '/js',
};

var webpackBundle = function(opts) {
    var webpackOptions = opts || {};

    webpackOptions.PROJECT_PATH = PROJECT_PATH;
    webpackOptions.debug = options.debug;

    return function(done) {
        var config = require('./webpack.config')(webpackOptions);

        webpack(config, function(err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log('[webpack]', stats.toString({ maxModules: Infinity, colors: true, optimizationBailout: true }));
            if (typeof done !== 'undefined' && (!opts || !opts.watch)) {
                done();
            }
        });
    };
};

gulp.task('bundle:watch', webpackBundle({ watch: true }));
gulp.task('bundle', webpackBundle());

gulp.task('watch', function() {
    gulp.start('bundle:watch');
});

gulp.task('default', ['watch']);
