/**
 * Stripe integration for NeuroLumina premium subscriptions.
 * Creates checkout sessions for the two premium tiers.
 *
 * Requires STRIPE_SECRET_KEY and NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
 * environment variables to be set (by the owner).
 */
import { createServerFn } from "@tanstack/react-start";
import { getCurrentUser } from "~/lib/auth";
import { sql } from "~/db";

// Price IDs — configured in Stripe dashboard
const PRICE_IDS = {
  premium_monthly: process.env.STRIPE_PRICE_PREMIUM_MONTHLY || "price_premium_monthly",
  enterprise_monthly: process.env.STRIPE_PRICE_ENTERPRISE_MONTHLY || "price_enterprise_monthly",
};

export type Tier = "premium" | "enterprise";

/** Create a Stripe Checkout Session for a given tier */
export const createCheckoutSession = createServerFn({ method: "POST" })
  .validator((data: { tier: Tier }) => {
    if (!["premium", "enterprise"].includes(data.tier)) {
      throw new Error("Invalid tier");
    }
    return data;
  })
  .handler(async ({ data }): Promise<{ ok: boolean; url?: string; error?: string }> => {
    try {
      const user = await getCurrentUser();
      if (!user) {
        return { ok: false, error: "Please sign in first" };
      }

      const Stripe = (await import("stripe")).default;
      const stripeKey = process.env.STRIPE_SECRET_KEY;
      if (!stripeKey) {
        // Demo mode — return a fake checkout URL
        return {
          ok: true,
          url: `/dashboard?upgrade=${data.tier}&demo=true`,
        };
      }

      const stripe = new Stripe(stripeKey, { apiVersion: "2025-02-24.acacia" as any });

      const priceId = data.tier === "premium"
        ? PRICE_IDS.premium_monthly
        : PRICE_IDS.enterprise_monthly;

      const session = await stripe.checkout.sessions.create({
        mode: "subscription",
        line_items: [{ price: priceId, quantity: 1 }],
        customer_email: user.email,
        success_url: `${process.env.SITE_URL || "https://neurolumina.dev"}/dashboard?success=true`,
        cancel_url: `${process.env.SITE_URL || "https://neurolumina.dev"}/pricing?cancelled=true`,
        metadata: {
          userId: String(user.userId),
          tier: data.tier,
        },
      });

      return { ok: true, url: session.url! };
    } catch (err) {
      console.error("Stripe checkout error:", err);
      return { ok: false, error: "Payment setup failed. Please try again." };
    }
  });

/** Handle Stripe webhook events (called from Stripe dashboard) */
export const handleStripeWebhook = createServerFn({ method: "POST" })
  .handler(async ({ request }): Promise<{ ok: boolean }> => {
    try {
      const body = await request.text();
      const signature = request.headers.get("stripe-signature") || "";

      const Stripe = (await import("stripe")).default;
      const stripeKey = process.env.STRIPE_SECRET_KEY;
      const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

      if (!stripeKey || !webhookSecret) {
        return { ok: true }; // Silently accept in dev mode
      }

      const stripe = new Stripe(stripeKey, { apiVersion: "2025-02-24.acacia" as any });
      const event = stripe.webhooks.constructEvent(body, signature, webhookSecret);

      if (event.type === "checkout.session.completed") {
        const session = event.data.object as any;
        const userId = Number(session.metadata?.userId);
        const tier = session.metadata?.tier || "premium";

        if (userId) {
          const db = sql();
          await db`
            UPDATE users SET tier = ${tier} WHERE id = ${userId}
          `;
        }
      }

      return { ok: true };
    } catch {
      return { ok: false };
    }
  });