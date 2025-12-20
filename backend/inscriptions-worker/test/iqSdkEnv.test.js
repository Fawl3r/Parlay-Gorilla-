const test = require("node:test");
const assert = require("node:assert/strict");

// Import the committed dist output to avoid requiring a TS build step during tests.
const { IqSdkEnv } = require("../dist/services/iq/IqSdkEnv.js");

function withTempEnv(overrides, fn) {
  const prev = {
    SIGNER_PRIVATE_KEY: process.env.SIGNER_PRIVATE_KEY,
    RPC: process.env.RPC,
  };

  try {
    if ("SIGNER_PRIVATE_KEY" in overrides) {
      const v = overrides.SIGNER_PRIVATE_KEY;
      if (v === undefined) delete process.env.SIGNER_PRIVATE_KEY;
      else process.env.SIGNER_PRIVATE_KEY = String(v);
    }
    if ("RPC" in overrides) {
      const v = overrides.RPC;
      if (v === undefined) delete process.env.RPC;
      else process.env.RPC = String(v);
    }

    fn();
  } finally {
    if (prev.SIGNER_PRIVATE_KEY === undefined) delete process.env.SIGNER_PRIVATE_KEY;
    else process.env.SIGNER_PRIVATE_KEY = prev.SIGNER_PRIVATE_KEY;

    if (prev.RPC === undefined) delete process.env.RPC;
    else process.env.RPC = prev.RPC;
  }
}

test("IqSdkEnv.assertRequired: throws when SIGNER_PRIVATE_KEY/RPC are missing", () => {
  withTempEnv({ SIGNER_PRIVATE_KEY: undefined, RPC: undefined }, () => {
    assert.throws(
      () => IqSdkEnv.assertRequired(),
      (err) => {
        assert.equal(err.name, "Error");
        assert.match(err.message, /SIGNER_PRIVATE_KEY/);
        assert.match(err.message, /RPC/);
        return true;
      }
    );
  });
});

test("IqSdkEnv.assertRequired: passes when SIGNER_PRIVATE_KEY/RPC are present", () => {
  // Use a base58-shaped string (no 0/O/I/l) long enough to look like a real key.
  withTempEnv({ SIGNER_PRIVATE_KEY: "11111111111111111111111111111111111111111111", RPC: "https://example.invalid" }, () => {
    assert.doesNotThrow(() => IqSdkEnv.assertRequired());
  });
});


