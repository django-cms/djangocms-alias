// #####################################################################################################################
// #IMPORTS#
const gulp = require('gulp');
const gutil = require('gulp-util');
const gulpif = require('gulp-if');
const sourcemaps = require('gulp-sourcemaps');
const webpack = require('webpack');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');
const cleanCSS = require('gulp-clean-css');
const autoprefixer = require('autoprefixer');
const flexbugs = require('postcss-flexbugs-fixes');
const initial = require('postcss-initial');
const watch = require('gulp-watch');

var argv = require('minimist')(process.argv.slice(2)); // eslint-disable-line

// #####################################################################################################################
// #SETTINGS#
var options = {
    debug: argv.debug,
};
var PROJECT_ROOT = __dirname + '/djangocms_alias/static/djangocms_alias';
var PROJECT_PATH = {
    js: PROJECT_ROOT + '/js',
    sass: PROJECT_ROOT + '/sass',
    css: PROJECT_ROOT + '/css',
};

var PROJECT_PATTERNS = {
    js: [PROJECT_PATH.js + '/*.js', '!' + PROJECT_PATH.js + '/dist/*.js'],
    sass: [PROJECT_PATH.sass + '/**/*.{scss,sass}'],
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

gulp.task('sass', function () {
    return gulp.src(PROJECT_PATTERNS.sass)
        .pipe(gulpif(argv.debug, sourcemaps.init()))
        .pipe(sass())
        .on('error', function (error) {
            gutil.log(gutil.colors.red(
                'Error (' + error.plugin + '): ' + error.messageFormatted)
            );

            if (process.env.EXIT_ON_ERRORS) {
                process.exit(1); // eslint-disable-line
            } else {
                // in dev mode - just continue
                this.emit('end');
            }
        })
        .pipe(
            postcss([
                initial,
                autoprefixer({
                    // browsers are coming from browserslist file
                    cascade: false,
                }),
                flexbugs,
            ])
        )
        .pipe(gulpif(!argv.debug, cleanCSS({
            rebase: false,
        })))
        .pipe(gulpif(argv.debug, sourcemaps.write()))
        .pipe(gulp.dest(PROJECT_PATH.css));
});

gulp.task('watch', function() {
    gulp.start('bundle:watch');

    watch(PROJECT_PATTERNS.sass, function () {
        return gulp.start('sass');
    });
});

gulp.task('default', ['watch']);
