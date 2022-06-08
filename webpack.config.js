var webpack = require('webpack');

module.exports = function (opts) {
    'use strict';

    var PROJECT_PATH = opts.PROJECT_PATH;
    var debug = opts.debug;

    if (!debug) {
        process.env.NODE_ENV = 'production';
    }

    var baseConfig = {
        mode: debug ? 'development' : 'production',
        devtool: false,
        watch: !!opts.watch,
        entry: {
            'alias.create': PROJECT_PATH.js + '/create.js',
        },
        output: {
            path: PROJECT_PATH.js + '/dist/',
            filename: 'bundle.[name].min.js',
            chunkFilename: 'bundle.[name].min.js',
            jsonpFunction: 'aliasWebpackJsonp'
        },
        plugins: [
        ],
        externals: {
            jquery: 'CMS.$',
        },
        module: {
            rules: [
                // must be first
                {
                    test: /\.js$/,
                    use: [{
                        loader: 'babel-loader',
                        options: {
                            retainLines: true
                        }
                    }],
                    exclude: /(node_modules|libs|addons\/jquery.*)/
                }
            ]
        },
        stats: 'verbose'
    };

    if (debug) {
        baseConfig.devtool = 'cheap-module-eval-source-map';
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.DefinePlugin({
                __DEV__: 'true'
            })
        ]);
    } else {
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.DefinePlugin({
                __DEV__: 'false'
            }),
            new webpack.optimize.ModuleConcatenationPlugin(),
        ]);
    }

    return baseConfig;
};
