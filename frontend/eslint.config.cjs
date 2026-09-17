module.exports = [{
  files: ['src/**/*.{js,jsx,ts,tsx}'],
  languageOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    globals: {
      // Browser globals
      window: 'readonly',
      document: 'readonly',
      navigator: 'readonly',
    },
    parserOptions: {
      ecmaFeatures: { jsx: true },
    },
  },
  plugins: {
    react: require('eslint-plugin-react'),
    'react-hooks': require('eslint-plugin-react-hooks'),
  },
  settings: {
    react: { version: 'detect' },
  },
  rules: {
    // React 17+ JSX transform
    'react/react-in-jsx-scope': 'off',
    // Prefer explicit props over spreading
    'react/jsx-props-no-spreading': 'warn',
  },
}];

