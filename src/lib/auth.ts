/**
 * Auth utilities for NeuroLumina premium subscriber authentication.
 * Uses JWT (via jose) for stateless sessions and scrypt for password hashing.
 * All functions are server-only (createServerFn or called from server code).
 */
import { createServerFn } from "@tanstack/react-start";
import { SignJWT, jwtVerify } from "jose";
import { sql } from "~/db";
import { scryptSync, randomBytes, timingSafeEqual } from "node:crypto";

// --- Constants ---

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "neuro-lumina-dev-secret-change-in-production",
);
const COOKIE_NAME = "nl_session";
const SESSION_DURATION = 60 * 60 * 24 * 7; // 7 days in seconds

// --- Password hashing ---

function hashPassword(password: string): string {
  const salt = randomBytes(16).toString("hex");
  const hash = scryptSync(password, salt, 64).toString("hex");
  return `${salt}:${hash}`;
}

function verifyPassword(password: string, stored: string): boolean {
  const [salt, key] = stored.split(":");
  const hash = scryptSync(password, salt, 64);
  const storedHash = Buffer.from(key, "hex");
  return storedHash.length === hash.length && timingSafeEqual(hash, storedHash);
}

// --- JWT helpers ---

async function createToken(userId: number, email: string, tier: string) {
  return await new SignJWT({ sub: String(userId), email, tier })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_DURATION}s`)
    .sign(JWT_SECRET);
}

async function verifyToken(token: string) {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return {
      userId: Number(payload.sub),
      email: payload.email as string,
      tier: (payload.tier as string) || "free",
    };
  } catch {
    return null;
  }
}

// --- Cookie helpers (works with the Request object in server functions) ---

function parseCookies(request: Request): Record<string, string> {
  const cookieHeader = request.headers.get("cookie") || "";
  return Object.fromEntries(
    cookieHeader.split(";").map((c) => {
      const [key, ...val] = c.trim().split("=");
      return [key, decodeURIComponent(val.join("="))];
    }).filter(([k]) => k),
  );
}

function setCookieHeader(name: string, value: string, maxAge: number): string {
  const secure = process.env.NODE_ENV === "production";
  return `${name}=${encodeURIComponent(value)}; HttpOnly; Secure=${secure ? "true" : ""}; SameSite=Lax; Max-Age=${maxAge}; Path=/`;
}

function deleteCookieHeader(name: string): string {
  return `${name}=; HttpOnly; Path=/; Max-Age=0`;
}

// --- Auth result type ---

export type AuthResult =
  | { ok: true; user: { id: number; email: string; tier: string } }
  | { ok: false; error: string };

// --- Cookie name export for client-side use ---

export { COOKIE_NAME };

/** Sign up a new user */
export const signup = createServerFn({ method: "POST" })
  .validator((data: { email: string; password: string }) => {
    const email = data.email?.trim().toLowerCase();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new Error("Valid email is required");
    }
    if (!data.password || data.password.length < 8) {
      throw new Error("Password must be at least 8 characters");
    }
    return { email, password: data.password };
  })
  .handler(async ({ data }): Promise<{ result: AuthResult; cookie?: string }> => {
    try {
      const db = sql();

      // Ensure tables exist
      await db`
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          tier TEXT NOT NULL DEFAULT 'free',
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
      `;

      // Check if user already exists
      const existing = await db`
        SELECT id FROM users WHERE email = ${data.email}
      `;
      if (existing.length > 0) {
        return { result: { ok: false, error: "An account with this email already exists" } };
      }

      const passwordHash = hashPassword(data.password);
      const result = await db`
        INSERT INTO users (email, password_hash, tier)
        VALUES (${data.email}, ${passwordHash}, 'free')
        RETURNING id, email, tier
      `;

      const user = result[0];
      const token = await createToken(user.id, user.email, user.tier);

      return {
        result: {
          ok: true,
          user: { id: user.id, email: user.email, tier: user.tier },
        },
        cookie: setCookieHeader(COOKIE_NAME, token, SESSION_DURATION),
      };
    } catch (err) {
      if (err instanceof Error && err.message.includes("DATABASE_URL")) {
        return { result: { ok: false, error: "Database not yet connected. Please try again later." } };
      }
      console.error("Signup error:", err);
      return { result: { ok: false, error: "Something went wrong. Please try again." } };
    }
  });

/** Log in an existing user */
export const login = createServerFn({ method: "POST" })
  .validator((data: { email: string; password: string }) => {
    const email = data.email?.trim().toLowerCase();
    if (!email) throw new Error("Email is required");
    if (!data.password) throw new Error("Password is required");
    return { email, password: data.password };
  })
  .handler(async ({ data }): Promise<{ result: AuthResult; cookie?: string }> => {
    try {
      const db = sql();
      const result = await db`
        SELECT id, email, password_hash, tier FROM users WHERE email = ${data.email}
      `;

      if (result.length === 0) {
        return { result: { ok: false, error: "Invalid email or password" } };
      }

      const user = result[0];
      if (!verifyPassword(data.password, user.password_hash)) {
        return { result: { ok: false, error: "Invalid email or password" } };
      }

      const token = await createToken(user.id, user.email, user.tier);

      return {
        result: {
          ok: true,
          user: { id: user.id, email: user.email, tier: user.tier },
        },
        cookie: setCookieHeader(COOKIE_NAME, token, SESSION_DURATION),
      };
    } catch (err) {
      if (err instanceof Error && err.message.includes("DATABASE_URL")) {
        return { result: { ok: false, error: "Database not yet connected. Please try again later." } };
      }
      console.error("Login error:", err);
      return { result: { ok: false, error: "Something went wrong. Please try again." } };
    }
  });

/** Get the currently logged-in user from the session cookie */
export const getCurrentUser = createServerFn({ method: "GET" })
  .handler(async ({ request }): Promise<{ userId: number; email: string; tier: string } | null> => {
    try {
      const cookies = parseCookies(request);
      const token = cookies[COOKIE_NAME];
      if (!token) return null;
      return await verifyToken(token);
    } catch {
      return null;
    }
  });

/** Log out — returns a delete-cookie header */
export const logout = createServerFn({ method: "POST" })
  .handler(async (): Promise<{ ok: true; cookie: string }> => {
    return { ok: true, cookie: deleteCookieHeader(COOKIE_NAME) };
  });
