import type { Pool } from "pg";

import type { Logger } from "../logging/logger";

export type VerificationRecordRow = {
  id: string;
  user_id: string;
  saved_parlay_id: string | null;
  data_hash: string;
  status: string;
  created_at: Date;
  confirmed_at: Date | null;
  tx_digest: string | null;
  object_id: string | null;
  network: string;
};

export class VerificationRecordsRepo {
  constructor(private readonly pool: Pool, private readonly logger: Logger) {}

  async getById(id: string): Promise<VerificationRecordRow | null> {
    const res = await this.pool.query<VerificationRecordRow>(
      `
      SELECT
        id,
        user_id,
        saved_parlay_id,
        data_hash,
        status,
        created_at,
        confirmed_at,
        tx_digest,
        object_id,
        network
      FROM verification_records
      WHERE id = $1
      LIMIT 1
      `,
      [id]
    );
    return res.rows[0] || null;
  }

  async markConfirmed(id: string, txDigest: string, objectId: string): Promise<void> {
    await this.pool.query(
      `
      UPDATE verification_records
      SET
        status = 'confirmed',
        tx_digest = $2,
        object_id = $3,
        error = NULL,
        confirmed_at = now()
      WHERE id = $1
      `,
      [id, txDigest, objectId]
    );
  }

  async setLastError(id: string, error: string): Promise<void> {
    const safe = String(error || "").slice(0, 500);
    await this.pool.query(
      `
      UPDATE verification_records
      SET error = $2
      WHERE id = $1
      `,
      [id, safe]
    );
  }

  async markFailed(id: string, error: string): Promise<void> {
    const safe = String(error || "").slice(0, 500);
    await this.pool.query(
      `
      UPDATE verification_records
      SET
        status = 'failed',
        error = $2
      WHERE id = $1
      `,
      [id, safe]
    );
    this.logger.warn({ id }, "marked verification record failed");
  }
}


