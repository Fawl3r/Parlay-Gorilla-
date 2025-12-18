import { Pool } from "pg";

export type SavedParlayRow = {
  id: string;
  user_id: string;
  account_number: string;
  parlay_type: string;
  content_hash: string;
  inscription_status: string;
  inscription_tx: string | null;
  created_at: string | null;
};

export class SavedParlaysRepo {
  private readonly pool: Pool;

  constructor(dbUrl: string) {
    this.pool = new Pool({ connectionString: dbUrl });
  }

  async close(): Promise<void> {
    await this.pool.end();
  }

  async getById(id: string): Promise<SavedParlayRow | null> {
    const res = await this.pool.query<SavedParlayRow>(
      `
      SELECT
        sp.id::text,
        sp.user_id::text,
        u.account_number,
        sp.parlay_type,
        sp.content_hash,
        sp.inscription_status,
        sp.inscription_tx,
        sp.created_at::text
      FROM saved_parlays sp
      JOIN users u ON u.id = sp.user_id
      WHERE sp.id = $1
      `,
      [id]
    );
    return res.rows[0] ?? null;
  }

  async markQueued(id: string): Promise<void> {
    await this.pool.query(
      `
      UPDATE saved_parlays
      SET inscription_status = 'queued',
          inscription_error = NULL,
          updated_at = now()
      WHERE id = $1
      `,
      [id]
    );
  }

  async markConfirmed(id: string, hash: string, txid: string): Promise<void> {
    await this.pool.query(
      `
      UPDATE saved_parlays
      SET inscription_status = 'confirmed',
          inscription_hash = $2,
          inscription_tx = $3,
          inscription_error = NULL,
          inscribed_at = now(),
          updated_at = now()
      WHERE id = $1
      `,
      [id, hash, txid]
    );
  }

  async markFailed(id: string, error: string): Promise<void> {
    await this.pool.query(
      `
      UPDATE saved_parlays
      SET inscription_status = 'failed',
          inscription_error = $2,
          updated_at = now()
      WHERE id = $1
      `,
      [id, error]
    );
  }
}


