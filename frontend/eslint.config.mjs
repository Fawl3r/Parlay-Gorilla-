import next from "eslint-config-next";

export default [
  {
    ignores: ["dist/**", ".pytest_cache/**"],
  },
  // Next 16+ ships `eslint-config-next` as a native flat config array.
  // Spreading it avoids FlatCompat + circular config issues.
  ...next,
  // Repo compatibility:
  // The current Next flat config enables a very strict set of React purity rules
  // that the existing codebase does not yet conform to. Keep lint usable by
  // disabling the high-noise rules (we still keep core Next/TS rules).
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/purity": "off",
      "react-hooks/immutability": "off",
      "react-hooks/refs": "off",
      "react-hooks/static-components": "off",
      "react-hooks/error-boundaries": "off",
      "react-hooks/use-memo": "off",
      "react-hooks/component-hook-factories": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/globals": "off",
      "react-hooks/config": "off",
      "react-hooks/gating": "off",
      "react-hooks/unsupported-syntax": "off",

      // Too noisy for the current codebase; can be re-enabled later.
      "react/no-unescaped-entities": "off",
    },
  },
];


