module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['react', 'react-hooks'],
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // Turn off the rule requiring React to be in scope (since we use React 17+ JSX transform)
    'react/react-in-jsx-scope': 'off',
    // Example: enforce consistent spacing for props
    'react/jsx-props-no-spreading': 'warn',
  },
};
