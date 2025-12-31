export type ParlayProofPayloadInput = {
  parlayId: string;
  accountNumber: string;
  hash: string;
  createdAtIso: string;
};

export type ParlayProofPayload = {
  type: "PARLAY_GORILLA_CUSTOM";
  schema: "pg_parlay_proof_v3";
  account_number: string;
  parlay_id: string;
  hash: string;
  created_at: string;
  website: string;
};

export function buildParlayProofPayload(input: ParlayProofPayloadInput): ParlayProofPayload {
  return {
    type: "PARLAY_GORILLA_CUSTOM",
    schema: "pg_parlay_proof_v3",
    account_number: input.accountNumber,
    parlay_id: input.parlayId,
    hash: input.hash,
    created_at: input.createdAtIso,
    website: "Visit ParlayGorilla.com",
  };
}

export function buildParlayProofDataString(input: ParlayProofPayloadInput): string {
  return JSON.stringify(buildParlayProofPayload(input));
}


