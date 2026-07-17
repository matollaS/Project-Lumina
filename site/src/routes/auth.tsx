import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { signup, login, COOKIE_NAME } from "~/lib/auth";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

/** Set a cookie on the client side (can't use HttpOnly, but works for our flow) */
function setClientCookie(name: string, value: string) {
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

function deleteClientCookie(name: string) {
  document.cookie = `${name}=; Path=/; Max-Age=0`;
}

function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? login : signup;
      const response = await fn({ data: { email, password } });

      if (response.result.ok) {
        // Store the session cookie client-side
        if (response.cookie) {
          // Parse the cookie value from the set-cookie header format
          const match = response.cookie.match(/nl_session=([^;]+)/);
          if (match) {
            setClientCookie(COOKIE_NAME, decodeURIComponent(match[1]));
          }
        }
        setSuccess(true);
        // Redirect to dashboard after short delay
        setTimeout(() => {
          router.navigate({ to: "/dashboard" });
        }, 800);
      } else {
        setError(response.result.error);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "signup" : "login");
    setError("");
  };

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
            href="/docs"
            className="text-sm text-gray-400 transition-colors hover:text-white"
          >
            Docs
          </a>
          <a
            href="/"
            className="text-sm text-gray-400 transition-colors hover:text-white"
          >
            Home
          </a>
        </div>
      </nav>

      {/* Auth form */}
      <section className="relative z-10 mx-auto mt-16 max-w-md px-6">
        <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-8 backdrop-blur-sm">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold tracking-tight">
              {mode === "login" ? "Welcome back" : "Create account"}
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              {mode === "login"
                ? "Sign in to your NeuroLumina account"
                : "Get started with NeuroLumina premium"}
            </p>
          </div>

          {success ? (
            <div className="rounded-xl border border-green-500/20 bg-green-500/10 p-6 text-center">
              <svg
                className="mx-auto h-10 w-10 text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                />
              </svg>
              <p className="mt-3 text-lg font-semibold text-white">
                {mode === "login" ? "Signed in!" : "Account created!"}
              </p>
              <p className="mt-1 text-sm text-gray-400">Redirecting to dashboard...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="email"
                  className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="you@lab.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-gray-700 bg-gray-900/60 px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition-all focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-gray-700 bg-gray-900/60 px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition-all focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                />
              </div>

              {error && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-full bg-gradient-to-r from-violet-600 to-cyan-500 px-6 py-3 text-sm font-semibold text-white transition-all hover:from-violet-500 hover:to-cyan-400 hover:shadow-lg hover:shadow-violet-500/30 disabled:opacity-50"
              >
                {loading
                  ? "Please wait..."
                  : mode === "login"
                    ? "Sign in"
                    : "Create account"}
              </button>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-gray-500">
            {mode === "login" ? (
              <>
                Don't have an account?{" "}
                <button
                  onClick={switchMode}
                  className="font-medium text-violet-400 transition-colors hover:text-violet-300"
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  onClick={switchMode}
                  className="font-medium text-violet-400 transition-colors hover:text-violet-300"
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-600">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </section>
    </div>
  );
}
