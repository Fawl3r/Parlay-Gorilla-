module parlay_gorilla::parlay_proof {
    use std::vector;

    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;

    /// Immutable verification record for a user-initiated custom parlay analysis.
    ///
    /// Notes:
    /// - Stores hashes only (no strings / no PII).
    /// - Frozen at creation to prevent mutation or transfer.
    struct Proof has key {
        id: UID,
        creator: address,
        data_hash: vector<u8>,
        created_at: u64,
    }

    const E_INVALID_HASH_LEN: u64 = 1;

    /// Create an immutable Proof object and freeze it.
    ///
    /// `data_hash` must be 32 bytes (SHA-256).
    public entry fun create_proof(data_hash: vector<u8>, created_at: u64, ctx: &mut TxContext) {
        assert!(vector::length(&data_hash) == 32, E_INVALID_HASH_LEN);

        let proof = Proof {
            id: object::new(ctx),
            creator: tx_context::sender(ctx),
            data_hash,
            created_at,
        };

        // Freeze to make the object immutable and ownerless.
        transfer::freeze_object(proof);
    }
}


