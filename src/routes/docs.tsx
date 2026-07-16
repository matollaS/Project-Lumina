import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/docs")({
  component: Docs,
});

function Docs() {
  return (
    <div className="min-h-dvh bg-gradient-to-b from-[#0f0b1a] via-[#140f26] to-[#0a0812] text-white">
      {/* Background glow */}
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
          <a
            href="/"
            className="text-sm text-gray-400 transition-colors hover:text-white"
          >
            Home
          </a>
          <a
            href="/#waitlist"
            className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-5 py-2 text-sm font-medium text-white transition-all hover:from-violet-500 hover:to-cyan-400"
          >
            Join waitlist
          </a>
        </div>
      </nav>

      {/* Header */}
      <section className="relative z-10 mx-auto mt-12 max-w-4xl px-6">
        <div className="mb-4">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
            Documentation
          </span>
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          NeuroLumina{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Platform Docs
          </span>
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-gray-400">
          Everything you need to get started with NeuroLumina — from loading your
          first SNIRF dataset to deploying pre-trained models in production.
        </p>
      </section>

      {/* Content */}
      <section className="relative z-10 mx-auto mt-12 max-w-4xl px-6 pb-24">
        <div className="flex flex-col gap-10">
          {/* Getting Started */}
          <SectionCard
            number="01"
            title="Getting Started"
            gradient="from-violet-500 to-purple-500"
          >
            <p className="mb-4 text-gray-400">
              NeuroLumina is an open-core AI platform for processing HD-fNIRS and
              PBM signals into real-time biophysical state intelligence.
            </p>
            <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-violet-300">
              Quick install
            </h4>
            <CodeBlock code="pip install neurolumina-core" lang="bash" />
            <h4 className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wider text-violet-300">
              First steps
            </h4>
            <ol className="list-inside list-decimal space-y-2 text-sm text-gray-400">
              <li>
                Load your SNIRF data using the built-in data loader (see{" "}
                <a href="#snirf-loader" className="text-violet-400 underline">
                  Data Loading
                </a>
                )
              </li>
              <li>
                Preprocess with motion correction, filtering, and chromophore
                conversion
              </li>
              <li>
                Extract features or run inference with pre-trained deep-learning
                models (Premium tier)
              </li>
              <li>
                Visualise results in real time via the NeuroLumina dashboard
              </li>
            </ol>
          </SectionCard>

          {/* Data Loading */}
          <SectionCard
            number="02"
            title="SNIRF Data Loading"
            gradient="from-cyan-500 to-teal-500"
            id="snirf-loader"
          >
            <p className="mb-4 text-gray-400">
              The open-core library provides a SNIRF-compatible data loader that
              works with any HD-fNIRS hardware, including Gowerlabs systems. It is
              designed to be MNE-Python friendly and integrates seamlessly with
              existing neuroscience workflows.
            </p>
            <CodeBlock
              code={`from neurolumina import load_snirf\nfrom neurolumina.preprocessing import (\n    motion_correct,\n    bandpass_filter,\n    chromophore_convert,\n)\n\n# Load your SNIRF file\nraw = load_snirf("recording.snirf")\n\n# Preprocess\nraw = motion_correct(raw)\nraw = bandpass_filter(raw, 0.01, 0.5)\nhbo, hbr = chromophore_convert(raw)`}
              lang="python"
            />
            <p className="mt-4 text-sm text-gray-500">
              The data loader supports both continuous-wave and frequency-domain
              fNIRS systems. See the{" "}
              <a
                href="https://github.com/neurolumina"
                target="_blank"
                rel="noopener noreferrer"
                className="text-violet-400 underline"
              >
                GitHub repository
              </a>{" "}
              for full API reference.
            </p>
          </SectionCard>

          {/* Preprocessing Pipeline */}
          <SectionCard
            number="03"
            title="Preprocessing Pipeline"
            gradient="from-indigo-500 to-violet-500"
          >
            <p className="mb-4 text-gray-400">
              The preprocessing module provides production-ready implementations of
              standard fNIRS processing steps:
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                {
                  title: "Motion Correction",
                  desc: "Wavelet-based and spline interpolation methods to remove motion artifacts from optical signals.",
                },
                {
                  title: "Bandpass Filtering",
                  desc: "Remove physiological noise (cardiac, respiratory) while preserving neural signals in the 0.01–0.5 Hz range.",
                },
                {
                  title: "Chromophore Conversion",
                  desc: "Modified Beer-Lambert law conversion from raw intensity to oxygenated (HbO) and deoxygenated (HbR) hemoglobin concentrations.",
                },
                {
                  title: "Artifact Rejection",
                  desc: "Automated detection and removal of channels contaminated by motion or poor optode coupling.",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-gray-800 bg-gray-900/40 p-4"
                >
                  <h4 className="mb-1 text-sm font-semibold text-white">
                    {item.title}
                  </h4>
                  <p className="text-xs leading-relaxed text-gray-400">
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Deep Learning Models */}
          <SectionCard
            number="04"
            title="Deep-Learning Models (Premium)"
            gradient="from-violet-500 to-cyan-500"
          >
            <p className="mb-4 text-gray-400">
              Premium subscribers get access to pre-trained CNN/Bi-LSTM
              architectures for cognitive state classification:
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-xs uppercase tracking-wider text-gray-500">
                    <th className="pb-3 pr-4 font-medium">Model</th>
                    <th className="pb-3 pr-4 font-medium">Task</th>
                    <th className="pb-3 font-medium">Input</th>
                  </tr>
                </thead>
                <tbody className="text-gray-400">
                  {[
                    {
                      model: "CogLoadNet",
                      task: "Cognitive load (3-class)",
                      input: "HbO/HbR time-series",
                    },
                    {
                      model: "FatigueNet",
                      task: "Fatigue regression (RMSE)",
                      input: "HbO/HbR + PSD features",
                    },
                    {
                      model: "RecoveryNet",
                      task: "Recovery index (0–100)",
                      input: "Multi-channel HbO/HbR",
                    },
                    {
                      model: "StateNet",
                      task: "Multi-state classification",
                      input: "Full HD-fNIRS montage",
                    },
                  ].map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-gray-800/50 last:border-0"
                    >
                      <td className="py-3 pr-4 font-medium text-white">
                        {row.model}
                      </td>
                      <td className="py-3 pr-4">{row.task}</td>
                      <td className="py-3 font-mono text-xs">{row.input}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>

          {/* API Reference */}
          <SectionCard
            number="05"
            title="Real-Time API Reference"
            gradient="from-cyan-500 to-blue-500"
          >
            <p className="mb-4 text-gray-400">
              The NeuroLumina Inference API provides real-time brain-state
              predictions via REST and WebSocket endpoints. Available in Premium
              and Enterprise tiers.
            </p>
            <h4 className="mb-2 text-sm font-semibold uppercase tracking-wider text-violet-300">
              REST Endpoint
            </h4>
            <CodeBlock
              code={`POST /api/v1/predict\nContent-Type: application/json\nAuthorization: Bearer <api-key>\n\n{\n  "channels": [\n    { "hbo": [0.12, 0.14, ...], "hbr": [0.08, 0.07, ...] }\n  ],\n  "model": "cog-load-net"\n}`}
              lang="json"
            />
            <h4 className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wider text-violet-300">
              Response
            </h4>
            <CodeBlock
              code={`{\n  "predictions": [\n    { "state": "focused", "confidence": 0.92 },\n    { "state": "fatigued", "confidence": 0.05 },\n    { "state": "neutral",  "confidence": 0.03 }\n  ],\n  "latency_ms": 12.4\n}`}
              lang="json"
            />
          </SectionCard>

          {/* Open Source */}
          <SectionCard
            number="06"
            title="Open-Source Contributions"
            gradient="from-green-500 to-emerald-500"
          >
            <p className="text-gray-400">
              The NeuroLumina open-core library is MIT-licensed and welcomes
              contributions. We follow standard GitHub flow — fork, branch, PR.
              All contributions must include tests and documentation.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <a
                href="https://github.com/neurolumina"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-gray-700 px-5 py-2 text-sm font-medium text-gray-300 transition-all hover:border-gray-500 hover:text-white"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                View on GitHub
              </a>
              <a
                href="mailto:hello@neurolumina.dev"
                className="inline-flex items-center gap-2 rounded-full border border-gray-700 px-5 py-2 text-sm font-medium text-gray-300 transition-all hover:border-gray-500 hover:text-white"
              >
                Get involved
              </a>
            </div>
          </SectionCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-violet-500 to-cyan-400">
              <span className="text-[10px] font-bold text-white">N</span>
            </div>
            <span>NeuroLumina Docs</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <a href="/" className="transition-colors hover:text-gray-300">
              Home
            </a>
            <a
              href="https://github.com/neurolumina"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-gray-300"
            >
              GitHub
            </a>
            <a
              href="mailto:hello@neurolumina.dev"
              className="transition-colors hover:text-gray-300"
            >
              Contact
            </a>
            <span className="text-gray-700">
              Built with{" "}
              <a href="https://cto.new" className="underline hover:text-gray-400">
                cto.new
              </a>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function SectionCard({
  number,
  title,
  children,
  gradient,
  id,
}: {
  number: string;
  title: string;
  children: React.ReactNode;
  gradient: string;
  id?: string;
}) {
  return (
    <div
      id={id}
      className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6 backdrop-blur-sm sm:p-8"
    >
      <div className="mb-4 flex items-center gap-3">
        <span
          className={`flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br ${gradient} text-xs font-bold`}
        >
          {number}
        </span>
        <h2 className="text-xl font-bold tracking-tight">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800 bg-gray-950/80">
      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-2">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {lang}
        </span>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code className="font-[family-name:var(--font-mono,monospace)] text-gray-300">
          {code}
        </code>
      </pre>
    </div>
  );
}
