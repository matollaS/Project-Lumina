import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { getCurrentUser, logout } from "~/lib/auth";
import { createApiKey, listApiKeys, revokeApiKey } from "~/lib/api-keys";
import { predict, listModels } from "~/lib/api-gateway";

export const Route = createFileRoute("/dashboard")({
  component: Dashboard,
  beforeLoad: async () => {
    const user = await getCurrentUser();
    return { user };
  },
});

function Dashboard() {
  const router = useRouter();
  const { user } = Route.useRouteContext();
  const [loggingOut, setLoggingOut] = useState(false);

  // API key management
  const [apiKeys, setApiKeys] = useState<Array<Record<string, unknown>>>([]);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [creatingKey, setCreatingKey] = useState(false);

  // API test console
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  // Tabs
  const [tab, setTab] = useState<"overview" | "keys" | "api">("overview");

  // If not authenticated, redirect to auth page
  if (!user) {
    router.navigate({ to: "/auth" });
    return null;
  }

  const handleLogout = async () => {
    setLoggingOut(true);
    const result = await logout();
    if (result.cookie) document.cookie = result.cookie;
    router.navigate({ to: "/" });
  };

  const handleCreateKey = async () => {
    setCreatingKey(true);
    const result = await createApiKey();
    if (result.ok) {
      setNewKey(result.key);
      // Refresh keys
      const keys = await listApiKeys();
      setApiKeys(keys);
    }
    setCreatingKey(false);
  };

  const handleRevokeKey = async (keyId: number) => {
    await revokeApiKey({ data: { keyId } });
    const keys = await listApiKeys();
    setApiKeys(keys);
  };

  const handleTestApi = async () => {
    setTestLoading(true);
    setTestResult(null);
    try {
      const result = await predict({
        data: {
          channels: [
            {
              hbo: Array.from({ length: 100 }, () => Math.random() * 0.3),
              hbr: Array.from({ length: 100 }, () => Math.random() * 0.2),
            },
          ],
          model: "cog-load-net",
        },
      });
      setTestResult(JSON.stringify(result, null, 2));
    } catch (err) {
      setTestResult(`Error: ${err}`);
    }
    setTestLoading(false);
  };

  const loadKeys = async () => {
    const keys = await listApiKeys();
    setApiKeys(keys);
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
          <a href="/pricing" className="text-sm text-gray-400 transition-colors hover:text-white">Pricing</a>
          <a href="/docs" className="text-sm text-gray-400 transition-colors hover:text-white">Docs</a>
          <button onClick={handleLogout} disabled={loggingOut} className="rounded-full border border-gray-700 px-4 py-1.5 text-xs text-gray-400 transition-all hover:border-gray-500 hover:text-white disabled:opacity-50">
            {loggingOut ? "..." : "Sign out"}
          </button>
        </div>
      </nav>

      <section className="relative z-10 mx-auto mt-8 max-w-5xl px-6 pb-24">
        {/* User header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 text-lg font-bold">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold">Dashboard</h1>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span>{user.email}</span>
                <span className="text-gray-700">·</span>
                <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs font-medium text-gray-400">
                  {user.tier === "premium" ? "Premium" : "Free"}
                </span>
              </div>
            </div>
          </div>
          <a href="/pricing" className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-5 py-2 text-sm font-medium text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/25">
            {user.tier === "premium" ? "Manage plan" : "Upgrade"}
          </a>
        </div>

        {/* Tabs */}
        <div className="mt-8 flex gap-1 rounded-xl border border-gray-800 bg-gray-900/40 p-1">
          {[
            { id: "overview" as const, label: "Overview" },
            { id: "keys" as const, label: "API Keys" },
            { id: "api" as const, label: "API Console" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => { setTab(t.id); if (t.id === "keys") loadKeys(); }}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                tab === t.id
                  ? "bg-violet-600/20 text-violet-300"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {tab === "overview" && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {[
              { title: "API Calls", value: "0 / 10,000", desc: "This month", color: "text-violet-400" },
              { title: "Models", value: "4", desc: "Available", color: "text-cyan-400" },
              { title: "Active Keys", value: String(apiKeys.length), desc: "API keys", color: "text-green-400" },
              { title: "Account Tier", value: user.tier === "premium" ? "Premium" : "Free", desc: user.tier === "premium" ? "Full access" : "Upgrade for more", color: "text-amber-400" },
            ].map((item, i) => (
              <div key={i} className="rounded-2xl border border-gray-800 bg-gray-900/40 p-5 backdrop-blur-sm">
                <p className="text-xs uppercase tracking-wider text-gray-500">{item.title}</p>
                <p className={`mt-1 text-2xl font-bold ${item.color}`}>{item.value}</p>
                <p className="mt-0.5 text-xs text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        )}

        {/* API Keys Tab */}
        {tab === "keys" && (
          <div className="mt-6">
            <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">API Keys</h2>
                  <p className="text-sm text-gray-500">Manage your inference API keys</p>
                </div>
                <button
                  onClick={handleCreateKey}
                  disabled={creatingKey}
                  className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-5 py-2 text-sm font-medium text-white transition-all hover:from-violet-500 hover:to-cyan-400 disabled:opacity-50"
                >
                  {creatingKey ? "Creating..." : "Create key"}
                </button>
              </div>

              {newKey && (
                <div className="mt-4 rounded-xl border border-green-500/20 bg-green-500/10 p-4">
                  <p className="text-sm font-medium text-green-400">New API Key Created</p>
                  <p className="mt-1 break-all font-mono text-xs text-green-300">{newKey}</p>
                  <p className="mt-1 text-xs text-green-500/80">Copy this now — you won't see it again!</p>
                  <button onClick={() => { setNewKey(null); }} className="mt-2 text-xs text-green-400 underline">Dismiss</button>
                </div>
              )}

              <div className="mt-4 space-y-2">
                {apiKeys.length === 0 ? (
                  <p className="py-4 text-center text-sm text-gray-500">
                    No API keys yet. Create one to get started.
                  </p>
                ) : (
                  apiKeys.map((key: any) => (
                    <div key={key.id} className="flex items-center justify-between rounded-xl border border-gray-800 bg-gray-950/50 px-4 py-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">{key.name}</span>
                          {key.active ? (
                            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                          ) : (
                            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                          )}
                        </div>
                        <p className="mt-0.5 font-mono text-xs text-gray-500">{key.prefix}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-600">
                          {new Date(key.created_at).toLocaleDateString()}
                        </span>
                        {key.active && (
                          <button
                            onClick={() => handleRevokeKey(key.id)}
                            className="text-xs text-red-400 transition-colors hover:text-red-300"
                          >
                            Revoke
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* API Console Tab */}
        {tab === "api" && (
          <div className="mt-6">
            <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-6 backdrop-blur-sm">
              <h2 className="text-lg font-semibold">API Console</h2>
              <p className="text-sm text-gray-500">Test the inference API with sample data</p>

              <div className="mt-4">
                <button
                  onClick={handleTestApi}
                  disabled={testLoading}
                  className="rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-6 py-2.5 text-sm font-medium text-white transition-all hover:from-violet-500 hover:to-cyan-400 disabled:opacity-50"
                >
                  {testLoading ? "Running inference..." : "Run test prediction"}
                </button>
              </div>

              {testResult && (
                <div className="mt-4 overflow-x-auto rounded-xl border border-gray-800 bg-gray-950/80 p-4">
                  <pre className="text-xs leading-relaxed text-gray-300">
                    <code>{testResult}</code>
                  </pre>
                </div>
              )}

              <div className="mt-6">
                <h3 className="mb-3 text-sm font-semibold text-gray-400">Available Models</h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    { id: "cog-load-net", name: "CogLoadNet", desc: "Cognitive load (3-class)", tier: "Premium" },
                    { id: "fatigue-net", name: "FatigueNet", desc: "Fatigue regression", tier: "Premium" },
                    { id: "recovery-net", name: "RecoveryNet", desc: "Recovery index", tier: "Premium" },
                    { id: "state-net", name: "StateNet", desc: "Multi-state classification", tier: "Enterprise" },
                  ].map((model, i) => (
                    <div key={i} className="flex items-center justify-between rounded-xl border border-gray-800 bg-gray-950/50 px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-white">{model.name}</p>
                        <p className="text-xs text-gray-500">{model.desc}</p>
                      </div>
                      <span className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-400">
                        {model.tier}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}