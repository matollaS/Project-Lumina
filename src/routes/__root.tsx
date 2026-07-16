import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRoute,
} from "@tanstack/react-router";
import type { ReactNode } from "react";

import favicon from "~/assets/favicon.svg?url";
import appCss from "~/styles/app.css?url";

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "NeuroLumina — Real-Time Brain State Intelligence" },
      {
        name: "description",
        content:
          "Open-core AI platform for HD-fNIRS and PBM signal processing. Real-time brain health, cognitive load, and recovery metrics for researchers, medtech startups, and human-performance programmes.",
      },
      {
        name: "keywords",
        content:
          "fNIRS, brain monitoring, cognitive load, neurotechnology, BCI, brain health, open-core AI",
      },
      { name: "theme-color", content: "#0f0b1a" },
      { property: "og:title", content: "NeuroLumina — Real-Time Brain State Intelligence" },
      {
        property: "og:description",
        content:
          "Open-core AI platform that processes HD-fNIRS and PBM signals into real-time biophysical state intelligence.",
      },
      { property: "og:type", content: "website" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", type: "image/svg+xml", href: favicon },
      {
        rel: "preconnect",
        href: "https://fonts.googleapis.com",
      },
      {
        rel: "preconnect",
        href: "https://fonts.gstatic.com",
        crossOrigin: "anonymous",
      },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap",
      },
    ],
  }),
  notFoundComponent: () => <div>Page not found</div>,
  component: RootComponent,
});

function RootComponent() {
  return (
    <RootDocument>
      <Outlet />
    </RootDocument>
  );
}

function RootDocument({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}