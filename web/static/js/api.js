/**
 * api.js - Asynchronous HTTP Fetch Wrappers with Defensive Error Handling
 * Connects the vanilla JS front-end to OSRM Python standard-library backend.
 */

import { showToast } from "./ui.js";

async function request(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    const isJson = res.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await res.json() : await res.text();

    if (!res.ok) {
      const errorMsg = data && data.error ? data.error : `HTTP Error ${res.status}`;
      const field = data && data.field ? ` [Field: ${data.field}]` : "";
      showToast(`${errorMsg}${field}`, "error");
      const err = new Error(errorMsg);
      err.field = data?.field;
      err.status = res.status;
      throw err;
    }

    return data;
  } catch (error) {
    if (error.name === "TypeError") {
      showToast("Network connection failed. Ensure OSRM server is active.", "error");
    }
    throw error;
  }
}

export const API = {
  getMeta: () => request("/api/meta"),
  getSamples: (module) => request(`/api/samples/${module}`),
  getSummary: () => request("/api/summary"),

  // Disk Scheduling
  runDisk: (payload) => request("/api/disk/run", { method: "POST", body: JSON.stringify(payload) }),
  compareDisk: (payload) => request("/api/disk/compare", { method: "POST", body: JSON.stringify(payload) }),

  // CPU Scheduling
  runCPU: (payload) => request("/api/cpu/run", { method: "POST", body: JSON.stringify(payload) }),
  compareCPU: (payload) => request("/api/cpu/compare", { method: "POST", body: JSON.stringify(payload) }),

  // Page Replacement
  runPages: (payload) => request("/api/pages/run", { method: "POST", body: JSON.stringify(payload) }),
  comparePages: (payload) => request("/api/pages/compare", { method: "POST", body: JSON.stringify(payload) }),
  getBelady: () => request("/api/pages/belady"),

  // Deadlock Avoidance
  evaluateSafety: (payload) => request("/api/deadlock/safety", { method: "POST", body: JSON.stringify(payload) }),
  evaluateRequest: (payload) => request("/api/deadlock/request", { method: "POST", body: JSON.stringify(payload) }),

  // System Diagnostics & Automation
  generateReport: (payload = { dataset: "large" }) => request("/api/report/generate", { method: "POST", body: JSON.stringify(payload) }),
  getLogsSummary: () => request("/api/logs/summary"),
  getSysinfo: () => request("/api/sysinfo"),
  runTests: () => request("/api/tests/run", { method: "POST", body: "{}" }),
};
