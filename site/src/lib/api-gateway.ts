/**
 * NeuroLumina Inference API Gateway.
 * Accepts HbO/HbR time-series data and returns brain-state predictions.
 * Stub implementation — returns mock predictions until production models are deployed.
 */
import { createServerFn } from "@tanstack/react-start";
import { getCurrentUser } from "~/lib/auth";

export type ChannelData = {
  hbo: number[];
  hbr: number[];
};

export type PredictRequest = {
  channels: ChannelData[];
  model: "cog-load-net" | "fatigue-net" | "recovery-net" | "state-net";
};

export type PredictResponse = {
  ok: boolean;
  predictions?: Array<{ state: string; confidence: number }>;
  latency_ms?: number;
  error?: string;
  model?: string;
};

// Mock model responses
const MOCK_PREDICTIONS: Record<string, Array<{ state: string; confidence: number }>> = {
  "cog-load-net": [
    { state: "focused", confidence: 0.72 },
    { state: "neutral", confidence: 0.18 },
    { state: "distracted", confidence: 0.10 },
  ],
  "fatigue-net": [
    { state: "alert", confidence: 0.65 },
    { state: "mild-fatigue", confidence: 0.25 },
    { state: "severe-fatigue", confidence: 0.10 },
  ],
  "recovery-net": [
    { state: "recovered", confidence: 0.58 },
    { state: "partial", confidence: 0.30 },
    { state: "depleted", confidence: 0.12 },
  ],
  "state-net": [
    { state: "cognitive-load", confidence: 0.45 },
    { state: "fatigue", confidence: 0.30 },
    { state: "recovery", confidence: 0.15 },
    { state: "resting", confidence: 0.10 },
  ],
};

/** Run inference on HD-fNIRS data */
export const predict = createServerFn({ method: "POST" })
  .validator((data: PredictRequest) => {
    if (!data.channels || !Array.isArray(data.channels) || data.channels.length === 0) {
      throw new Error("At least one channel is required");
    }
    if (!data.model || !MOCK_PREDICTIONS[data.model]) {
      throw new Error(`Invalid model. Choose: ${Object.keys(MOCK_PREDICTIONS).join(", ")}`);
    }
    return data;
  })
  .handler(async ({ data }): Promise<PredictResponse> => {
    // Check auth (optional for now — will be required in production)
    const user = await getCurrentUser();

    // Simulate processing latency (10-50ms)
    const startTime = Date.now();
    await new Promise((r) => setTimeout(r, 10 + Math.random() * 40));

    const latency = Date.now() - startTime;
    const predictions = MOCK_PREDICTIONS[data.model];

    return {
      ok: true,
      model: data.model,
      predictions,
      latency_ms: latency,
    };
  });

/** List available models with metadata */
export const listModels = createServerFn({ method: "GET" }).handler(async () => {
  return [
    {
      id: "cog-load-net",
      name: "CogLoadNet",
      description: "Cognitive load classification (3-class)",
      input: "HbO/HbR time-series",
      tier: "premium",
      status: "available",
    },
    {
      id: "fatigue-net",
      name: "FatigueNet",
      description: "Fatigue regression",
      input: "HbO/HbR + PSD features",
      tier: "premium",
      status: "available",
    },
    {
      id: "recovery-net",
      name: "RecoveryNet",
      description: "Recovery index (0–100)",
      input: "Multi-channel HbO/HbR",
      tier: "premium",
      status: "available",
    },
    {
      id: "state-net",
      name: "StateNet",
      description: "Multi-state classification",
      input: "Full HD-fNIRS montage",
      tier: "enterprise",
      status: "coming-soon",
    },
  ];
});