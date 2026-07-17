import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { submitToWaitlist } from "~/lib/waitlist";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    try {
      const result = await submitToWaitlist({ data: { email } });
      if (result.ok) {
        setSubmitted(true);
      } else {
        alert(result.message || "Something went wrong. Please try again.");
      }
    } catch {
      alert("Unable to connect. Please try again later.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-dvh overflow-hidden bg-gradient-to-b from-[#0f0b1a] via-[#140f26] to-[#0a0812] text-white">
      {/* Background glow effects */}
      <div className="pointer-events-none absolute -left-64 -top-64 h-[500px] w-[500px] rounded-full bg-violet-600/20 blur-[120px]" />
      <div className="pointer-events-none absolute -right-64 top-1/3 h-[400px] w-[400px] rounded-full bg-cyan-500/15 blur-[100px]" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-[350px] w-[350px] rounded-full bg-indigo-600/10 blur-[90px]" />

      {/* Navigation */}
      <nav className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-400">
            <span className="text-xs font-bold text-white">N</span>
          </div>
          <span className="text-lg font-bold tracking-tight">NeuroLumina</span>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="/pricing"
            className="hidden text-sm text-gray-400 transition-colors hover:text-white sm:block"
          >
            Pricing
          </a>
          <a
            href="/docs"
            className="hidden text-sm text-gray-400 transition-colors hover:text-white sm:block"
          >
            Docs
          </a>
          <a
            href="#tiers"
            className="hidden text-sm text-gray-400 transition-colors hover:text-white sm:block"
          >
            Tiers
          </a>
          <a
            href="#audience"
            className="hidden text-sm text-gray-400 transition-colors hover:text-white sm:block"
          >
            For whom
          </a>
          <a
            href="/auth"
            className="hidden text-sm text-gray-400 transition-colors hover:text-white sm:block"
          >
            Sign in
          </a>
          <a
            href="#waitlist"
            className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-5 py-2 text-sm font-medium text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/25"
          >
            Join waitlist
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 mx-auto mt-16 max-w-5xl px-6 text-center sm:mt-24">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
          Open-core AI platform — now in early access
        </div>
        <h1 className="bg-gradient-to-b from-white via-white to-gray-400 bg-clip-text text-5xl font-extrabold leading-tight tracking-tight text-transparent sm:text-6xl sm:leading-tight lg:text-7xl">
          Real-Time{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Brain State
          </span>{" "}
          Intelligence
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-400 sm:text-xl">
          Turn HD-fNIRS and PBM signals into actionable biophysical metrics — brain
          health, cognitive load, recovery — with an open-core AI platform built for
          researchers, medtech startups, and human-performance programmes.
        </p>
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="#waitlist"
            className="w-full rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-8 py-3 text-base font-semibold text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/30 sm:w-auto"
          >
            Get early access
          </a>
          <a
            href="#tiers"
            className="w-full rounded-full border border-gray-700 px-8 py-3 text-base font-medium text-gray-300 transition-all hover:border-gray-500 hover:text-white sm:w-auto"
          >
            See plans
          </a>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="relative z-10 mx-auto mt-32 max-w-6xl px-6">
        <div className="mb-4 text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
            The platform
          </span>
        </div>
        <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
          From raw signal to{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            biophysical insight
          </span>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
          NeuroLumina bridges the gap between complex optical brain signals and the
          real-world metrics that matter — no signal-processing PhD required.
        </p>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {[
            {
              icon: (
                <svg
                  className="h-6 w-6 text-violet-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                  />
                </svg>
              ),
              title: "SNIRF-Compatible Pipeline",
              desc: "Open-source data loaders and preprocessing (motion correction, filtering, chromophore conversion) that work with any HD-fNIRS hardware."
            },
            {
              icon: (
                <svg
                  className="h-6 w-6 text-cyan-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605"
                  />
                </svg>
              ),
              title: "Pre-Trained Deep Models",
              desc: "CNN/Bi-LSTM architectures for cognitive load classification, fatigue detection, and recovery metrics — available in the premium tier."
            },
            {
              icon: (
                <svg
                  className="h-6 w-6 text-indigo-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"
                  />
                </svg>
              ),
              title: "Real-Time API & Dashboards",
              desc: "Plug-and-play inference API for live brain-state monitoring, with turnkey dashboards for clinical and performance applications."
            },
          ].map((item, i) => (
            <div
              key={i}
              className="group rounded-2xl border border-gray-800 bg-gray-900/50 p-6 backdrop-blur-sm transition-all hover:border-violet-500/30 hover:bg-gray-900/80"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gray-800 group-hover:bg-gray-700/50">
                {item.icon}
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm leading-relaxed text-gray-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Open Core + Premium Tiers */}
      <section id="tiers" className="relative z-10 mx-auto mt-32 max-w-6xl px-6">
        <div className="mb-4 text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
            Pricing
          </span>
        </div>
        <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
          Open core.{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Premium power.
          </span>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
          Start with the free open-core library. Upgrade when you need production-grade
          models, real-time inference, and dedicated support.
        </p>
        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {/* Open Core */}
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-8 backdrop-blur-sm">
            <div className="mb-2 flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gray-700">
                <svg className="h-3.5 w-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 0 0-1.883 2.542l.857 6a2.25 2.25 0 0 0 2.227 1.932H19.05a2.25 2.25 0 0 0 2.227-1.932l.857-6a2.25 2.25 0 0 0-1.883-2.542m-16.5 0V6A2.25 2.25 0 0 1 6 3.75h3.879a1.5 1.5 0 0 1 1.06.44l2.122 2.12a1.5 1.5 0 0 0 1.06.44H18A2.25 2.25 0 0 1 20.25 9v.776" />
                </svg>
              </div>
              <span className="text-lg font-semibold">Open Core</span>
            </div>
            <p className="mt-1 text-3xl font-bold">
              Free
              <span className="text-base font-normal text-gray-500"> — forever</span>
            </p>
            <ul className="mt-6 space-y-3">
              {[
                "SNIRF-compatible data loaders",
                "Preprocessing pipeline (motion correction, filtering, chromophore conversion)",
                "Reference implementations in Python (MNE-Python friendly)",
                "GitHub repository with CI/CD and contribution guidelines",
                "MIT License",
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
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              View on GitHub
            </a>
          </div>

          {/* Premium */}
          <div className="relative rounded-2xl border border-violet-500/30 bg-gradient-to-b from-violet-900/20 to-gray-900/40 p-8 backdrop-blur-sm">
            <div className="absolute -top-3 right-6 rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider">
              Popular
            </div>
            <div className="mb-2 flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-cyan-500">
                <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
                </svg>
              </div>
              <span className="text-lg font-semibold">Premium</span>
            </div>
            <p className="mt-1 text-3xl font-bold">
              $200
              <span className="text-base font-normal text-gray-400">/mo</span>
              <span className="ml-2 text-base font-normal text-gray-500">– $2,000/mo</span>
            </p>
            <ul className="mt-6 space-y-3">
              {[
                "Everything in Open Core, plus:",
                "Pre-trained CNN/Bi-LSTM deep-learning models",
                "Real-time inference API (REST + WebSocket)",
                "Custom dashboard builder",
                "Priority support & SLAs",
                "Enterprise: on-premise deployment, white-label, dedicated model training",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                  <svg
                    className={`mt-0.5 h-4 w-4 shrink-0 ${i === 0 ? "text-violet-400" : "text-cyan-400"}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d={i === 0 ? "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" : "m4.5 12.75 6 6 9-13.5"}
                    />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <a
              href="#waitlist"
              className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-6 py-3 text-sm font-semibold text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/30"
            >
              Get early access
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </a>
          </div>
        </div>
      </section>

      {/* Target Audience */}
      <section id="audience" className="relative z-10 mx-auto mt-32 max-w-6xl px-6">
        <div className="mb-4 text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
            For whom
          </span>
        </div>
        <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
          Built for{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            pioneers
          </span>{" "}
          in brain science
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
          From bench to bedside to battlefield — NeuroLumina serves the teams pushing
          the boundaries of optical brain monitoring.
        </p>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {[
            {
              emoji: "🔬",
              title: "Neuroscience Labs & BCI Researchers",
              desc: "Reproducible, production-grade analysis pipelines for Gowerlabs and similar HD-fNIRS hardware. SNIRF-compatible, MNE-Python friendly.",
              stats: "Primary audience",
            },
            {
              emoji: "🧠",
              title: "Wearable Medtech Startups",
              desc: "Plug-and-play brain-state analytics for consumer and professional headsets — focus, fatigue, and recovery metrics out of the box.",
              stats: "Secondary audience",
            },
            {
              emoji: "⚡",
              title: "Human-Performance Programmes",
              desc: "Optical brain monitoring for military, esports, and high-stress operations. Real-time cognitive state tracking for peak performance.",
              stats: "Enterprise tier",
            },
          ].map((item, i) => (
            <div
              key={i}
              className="group rounded-2xl border border-gray-800 bg-gray-900/50 p-6 backdrop-blur-sm transition-all hover:border-cyan-500/30 hover:bg-gray-900/80"
            >
              <span className="mb-4 block text-3xl">{item.emoji}</span>
              <h3 className="mb-2 text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm leading-relaxed text-gray-400">{item.desc}</p>
              <span className="mt-4 inline-block rounded-full bg-gray-800 px-3 py-1 text-xs font-medium text-gray-500">
                {item.stats}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Waitlist / Signup CTA */}
      <section id="waitlist" className="relative z-10 mx-auto mt-32 mb-24 max-w-3xl px-6">
        <div className="rounded-3xl border border-violet-500/20 bg-gradient-to-b from-violet-900/20 to-gray-900/40 p-8 text-center backdrop-blur-sm sm:p-12">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Get early access to{" "}
            <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
              NeuroLumina
            </span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-gray-400">
            Join the waitlist for early access to the open-core library, premium beta,
            and exclusive research community updates.
          </p>

          {submitted ? (
            <div className="mx-auto mt-8 max-w-md rounded-xl border border-green-500/20 bg-green-500/10 p-6">
              <svg className="mx-auto h-10 w-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              <p className="mt-3 text-lg font-semibold text-white">You're on the list!</p>
              <p className="mt-1 text-sm text-gray-400">
                We'll be in touch with early access details and community updates.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mx-auto mt-8 flex max-w-md flex-col gap-3 sm:flex-row">
              <input
                type="email"
                required
                placeholder="you@lab.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 rounded-full border border-gray-700 bg-gray-900/60 px-5 py-3 text-sm text-white placeholder-gray-500 outline-none transition-all focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
              />
              <button
                type="submit"
                disabled={submitting}
                className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-6 py-3 text-sm font-semibold text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/30 disabled:opacity-50"
              >
                {submitting ? "Joining..." : "Join waitlist"}
              </button>
            </form>
          )}

          <p className="mt-4 text-xs text-gray-500">
            No spam. Unsubscribe at any time.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-violet-500 to-cyan-400">
              <span className="text-[10px] font-bold text-white">N</span>
            </div>
            <span>NeuroLumina</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <a
              href="/pricing"
              className="transition-colors hover:text-gray-300"
            >
              Pricing
            </a>
            <a
              href="/docs"
              className="transition-colors hover:text-gray-300"
            >
              Docs
            </a>
            <a
              href="/dashboard"
              className="transition-colors hover:text-gray-300"
            >
              Dashboard
            </a>
            <a
              href="/auth"
              className="transition-colors hover:text-gray-300"
            >
              Sign in
            </a>
            <a
              href="https://github.com/neurolumina"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-gray-300"
            >
              GitHub
            </a>
            <a href="mailto:hello@neurolumina.dev" className="transition-colors hover:text-gray-300">
              Contact
            </a>
            <span className="text-gray-700">
              Built with{" "}
              <a
                href="https://cto.new"
                className="underline hover:text-gray-400"
              >
                cto.new
              </a>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}