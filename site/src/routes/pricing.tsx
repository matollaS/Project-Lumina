import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { createCheckoutSession } from "~/lib/stripe";
import type { Tier } from "~/lib/stripe";

export const Route = createFileRoute("/pricing")({
  component: PricingPage,
});

function PricingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<Tier | null>(null);
  const [error, setError] = useState("");

  const handleSubscribe = async (tier: Tier) => {
    setLoading(tier);
    setError("");
    try {
      const result = await createCheckoutSession({ data: { tier } });
      if (result.ok && result.url) {
        router.navigate({ to: result.url });
      } else {
        setError(result.error || "Something went wrong");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-dvh bg-gradient-to-b from-[#0f0b1a] via-[#140f26] to-[#0a0812] text-white">
      <div className="pointer-events-none fixed -left-64 -top-64 h-[500px] w-[500px] rounded-full bg-violet-600/20 blur-[120px]" />
      <div className="pointer-events-none fixed -right-64 bottom-0 h-[400px] w-[400px] rounded-full bg-cyan-500/10 blur-[100px]" />

      {/* Nav */}
      <nav className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <a href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-400">
            <span className="text-xs font-bold text-white">N</span>
          </div>
          <span className="text-lg font-bold tracking-tight">NeuroLumina</span>
        </a>
        <div className="flex items-center gap-4">
          <a href="/docs" className="text-sm text-gray-400 transition-colors hover:text-white">Docs</a>
          <a href="/auth" className="text-sm text-gray-400 transition-colors hover:text-white">Sign in</a>
        </div>
      </nav>

      <section className="relative z-10 mx-auto mt-16 max-w-5xl px-6">
        <div className="mb-4 text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">Pricing</span>
        </div>
        <h1 className="text-center text-4xl font-extrabold tracking-tight sm:text-5xl">
          Choose your{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            plan
          </span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-center text-gray-400">
          Start with the free open-core library. Upgrade to premium for production-grade
          models, real-time inference, and dedicated support.
        </p>

        {error && (
          <div className="mx-auto mt-6 max-w-md rounded-xl border border-red-500/20 bg-red-500/10 px-6 py-3 text-center text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {/* Free */}
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-8 backdrop-blur-sm">
            <h2 className="text-lg font-semibold">Open Core</h2>
            <p className="mt-1 text-3xl font-bold">
              $0
              <span className="text-base font-normal text-gray-500">/mo</span>
            </p>
            <p className="mt-2 text-sm text-gray-500">Forever free</p>
            <ul className="mt-6 space-y-3">
              {[
                "SNIRF-compatible data loaders",
                "Preprocessing pipeline",
                "Python reference implementations",
                "MIT License",
                "Community support",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                  <svg className="mt-0.5 h-4 w-4 shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <a
              href="https://github.com/neurolumina"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full border border-gray-700 px-6 py-3 text-sm font-medium text-gray-300 transition-all hover:border-gray-500 hover:text-white"
            >
              View on GitHub
            </a>
          </div>

          {/* Premium - $200/mo */}
          <div className="relative rounded-2xl border border-violet-500/30 bg-gradient-to-b from-violet-900/20 to-gray-900/40 p-8 backdrop-blur-sm">
            <div className="absolute -top-3 right-6 rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider">
              Popular
            </div>
            <h2 className="text-lg font-semibold">Premium</h2>
            <p className="mt-1 text-3xl font-bold">
              $200
              <span className="text-base font-normal text-gray-400">/mo</span>
            </p>
            <p className="mt-2 text-sm text-gray-500">For labs and startups</p>
            <ul className="mt-6 space-y-3">
              {[
                "Everything in Open Core",
                "Pre-trained CNN/Bi-LSTM models",
                "Real-time inference API",
                "10,000 API calls/month",
                "Custom dashboard builder",
                "Priority email support",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                  <svg className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleSubscribe("premium")}
              disabled={loading === "premium"}
              className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-6 py-3 text-sm font-semibold text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/30 disabled:opacity-50"
            >
              {loading === "premium" ? "Redirecting..." : "Subscribe — $200/mo"}
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>

          {/* Enterprise - $2,000/mo */}
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-8 backdrop-blur-sm">
            <h2 className="text-lg font-semibold">Enterprise</h2>
            <p className="mt-1 text-3xl font-bold">
              $2,000
              <span className="text-base font-normal text-gray-400">/mo</span>
            </p>
            <p className="mt-2 text-sm text-gray-500">For organizations</p>
            <ul className="mt-6 space-y-3">
              {[
                "Everything in Premium",
                "100,000 API calls/month",
                "On-premise deployment",
                "White-label dashboards",
                "Dedicated model training",
                "SLA & phone support",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                  <svg className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleSubscribe("enterprise")}
              disabled={loading === "enterprise"}
              className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full border border-violet-500/50 px-6 py-3 text-sm font-semibold text-violet-300 transition-all hover:bg-violet-500/10 hover:text-white disabled:opacity-50"
            >
              {loading === "enterprise" ? "Redirecting..." : "Subscribe — $2,000/mo"}
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </button>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-gray-600">
          All plans include the MIT-licensed open-core library. Enterprise includes
          on-premise deployment and dedicated support.
        </p>
      </section>
    </div>
  );
}