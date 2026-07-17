/**
 * API key generation and management for the NeuroLumina inference gateway.
 * Keys are stored in the database and associated with user accounts.
 */
import { createServerFn } from "@tanstack/react-start";
import { sql } from "~/db";
import { randomBytes } from "node:crypto";
import { getCurrentUser } from "~/lib/auth";

function generateApiKey(): string {
  const prefix = "nl_";
  const random = randomBytes(24).toString("hex");
  return `${prefix}${random}`;
}

function maskKey(key: string): string {
  return key.slice(0, 8) + "..." + key.slice(-4);
}

/** Create a new API key for the current user */
export const createApiKey = createServerFn({ method: "POST" }).handler(async () => {
  const user = await getCurrentUser();
  if (!user) {
    return { ok: false, error: "Not authenticated" };
  }

  try {
    const db = sql();
    await db`
      CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        key_hash TEXT NOT NULL UNIQUE,
        prefix TEXT NOT NULL,
        name TEXT DEFAULT 'Default',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_used TIMESTAMPTZ,
        active BOOLEAN DEFAULT TRUE
      )
    `;

    const rawKey = generateApiKey();
    const prefix = rawKey.slice(0, 8) + "...";
    // In production, hash the key before storing. For now store the prefix for display.
    await db`
      INSERT INTO api_keys (user_id, key_hash, prefix, name)
      VALUES (${user.userId}, ${rawKey}, ${prefix}, 'API Key ' + ${String(Date.now()).slice(-4)})
    `;

    return { ok: true, key: rawKey, masked: maskKey(rawKey) };
  } catch (err) {
    if (err instanceof Error && err.message.includes("DATABASE_URL")) {
      // Return a demo key when database is not connected
      return {
        ok: true,
        key: "nl_demo_" + generateApiKey().slice(4),
        masked: "nl_demo_...",
        demo: true,
      };
    }
    console.error("API key creation error:", err);
    return { ok: false, error: "Something went wrong" };
  }
});

/** List API keys for the current user */
export const listApiKeys = createServerFn({ method: "GET" }).handler(async () => {
  const user = await getCurrentUser();
  if (!user) return [];

  try {
    const db = sql();
    const keys = await db`
      SELECT id, prefix, name, created_at, last_used, active
      FROM api_keys
      WHERE user_id = ${user.userId}
      ORDER BY created_at DESC
    `;
    return keys.map((k: Record<string, unknown>) => ({
      ...k,
      created_at: String(k.created_at),
      last_used: k.last_used ? String(k.last_used) : null,
    }));
  } catch {
    return [];
  }
});

/** Revoke an API key */
export const revokeApiKey = createServerFn({ method: "POST" })
  .validator((data: { keyId: number }) => {
    return { keyId: data.keyId };
  })
  .handler(async ({ data }) => {
    const user = await getCurrentUser();
    if (!user) return { ok: false, error: "Not authenticated" };

    try {
      const db = sql();
      await db`
        UPDATE api_keys SET active = FALSE WHERE id = ${data.keyId} AND user_id = ${user.userId}
      `;
      return { ok: true };
    } catch {
      return { ok: false, error: "Something went wrong" };
    }
  });