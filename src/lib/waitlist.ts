/**
 * Server-only database operations for the waitlist.
 * Used via createServerFn from page components.
 */
import { createServerFn } from "@tanstack/react-start";
import { sql } from "~/db";

export const submitToWaitlist = createServerFn({ method: "POST" })
  .validator((data: { email: string }) => {
    const email = data.email?.trim().toLowerCase();
    if (!email) throw new Error("Email is required");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      throw new Error("Invalid email address");
    return { email };
  })
  .handler(async ({ data }) => {
    try {
      const db = sql();

      // Ensure the waitlist table exists (idempotent)
      await db`
        CREATE TABLE IF NOT EXISTS waitlist (
          id SERIAL PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          source TEXT DEFAULT 'website',
          subscribed BOOLEAN DEFAULT TRUE
        )
      `;

      // Insert the email
      const result = await db`
        INSERT INTO waitlist (email, created_at)
        VALUES (${data.email}, NOW())
        ON CONFLICT (email) DO NOTHING
        RETURNING id
      `;

      return {
        ok: true,
        message: result.length > 0
          ? "Successfully joined waitlist!"
          : "You're already on the list!",
      };
    } catch (err) {
      if (
        err instanceof Error &&
        err.message.includes("DATABASE_URL")
      ) {
        return {
          ok: false,
          message:
            "Database not yet connected — we've noted your interest. We'll be in touch soon!",
        };
      }
      console.error("Waitlist error:", err);
      return { ok: false, message: "Something went wrong. Please try again." };
    }
  });
