var path = require('path');
var webpack = require('webpack')

module.exports = {
  entry: './renderer/index.js',
  output: { path: __dirname + '/build/', filename: 'bundle.js' },
  target: 'atom',
  module: {
    loaders: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        query: {
          presets: ['es2015', 'react'],
          plugins: [ 'transform-object-rest-spread', 'transform-regenerator' ]
        }
      },
      {
        test: /\.json$/,
        loader: 'json-loader'
      }
    ]
  },
  plugins: [
    new webpack.DefinePlugin({
      VERSION: JSON.stringify(require('./package.json').version)
    }),
    new webpack.DefinePlugin({
      "global.GENTLY": false
    }),
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': '"production"'
      }
    })
  ]
};
