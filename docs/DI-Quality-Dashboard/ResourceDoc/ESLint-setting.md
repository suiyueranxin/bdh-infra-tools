# ESLint Setting

```
module.exports = {

  'env': {

    'browser': true,

    'es6': true,

  },

  'extends': [

    'google',

  ],

  'globals': {

    'Atomics': 'readonly',

    'SharedArrayBuffer': 'readonly',

  },

  'parserOptions': {

    'ecmaVersion': 2018,

    'sourceType': 'module',

  },

  'rules': {

    'max-len': ['error', {'code': 100}],

    'linebreak-style': ['error', 'windows']

  },

};
```
