/**
 * app.js - Application Orchestrator & Client-side Route Dispatcher
 * Sets up the deterministic noise grain backdrop tile and view router.
 */

import { renderDashboard } from "./views/dashboard.js";
import { renderDiskView } from "./views/disk.js";
import { renderCPUView } from "./views/cpu.js";
import { renderPagesView } from "./views/pages.js";
import { renderDeadlockView } from "./views/deadlock.js";
import { renderToolsView } from "./views/tools.js";

// Deterministic Mulberry32 PRNG for grain synthesis
function createMulberry32(seed) {
  let s = seed | 0;
  return function() {
    s = (s + 0x6D2B79F5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Generate 160x160 grain tile pattern and apply as background
function generateGrainTile() {
  const canvas = document.createElement("canvas");
  canvas.width = 160;
  canvas.height = 160;
  const ctx = canvas.getContext("2d");
  const imgData = ctx.createImageData(160, 160);
  const data = imgData.data;

  const rng = createMulberry32(424242);
  const amplitude = 1.7;

  for (let i = 0; i < data.length; i += 4) {
    // 3-sample averaged random
    const sample = (rng() + rng() + rng()) / 3.0;
    const noise = Math.round((sample - 0.5) * amplitude * 18);
    const val = Math.min(255, Math.max(0, 10 + noise));

    data[i] = val;
    data[i + 1] = val + 2;
    data[i + 2] = val + 8;
    data[i + 3] = 40; // semi-transparent overlay
  }

  ctx.putImageData(imgData, 0, 0);
  const dataUrl = canvas.toDataURL("image/png");
  document.body.style.backgroundImage = `url("${dataUrl}")`;
  document.body.style.backgroundRepeat = "repeat";
}

// Client-Side Router
class AppRouter {
  constructor(viewportEl) {
    this.viewport = viewportEl;
    this.routes = {
      dashboard: renderDashboard,
      disk: renderDiskView,
      cpu: renderCPUView,
      pages: renderPagesView,
      deadlock: renderDeadlockView,
      tools: renderToolsView,
    };
    this.currentRoute = null;
  }

  init() {
    window.addEventListener("hashchange", () => this.handleHashChange());
    const initialRoute = window.location.hash.replace("#", "") || "dashboard";
    this.navigate(initialRoute);
  }

  navigate(route) {
    if (!this.routes[route]) route = "dashboard";
    window.location.hash = `#${route}`;
  }

  async handleHashChange() {
    const route = window.location.hash.replace("#", "") || "dashboard";
    if (!this.routes[route]) return this.navigate("dashboard");

    this.currentRoute = route;

    // Update Nav Pills Active Class
    document.querySelectorAll(".nav-pill").forEach(pill => {
      const target = pill.getAttribute("data-route");
      if (target === route) {
        pill.classList.add("active");
      } else {
        pill.classList.remove("active");
      }
    });

    // Render View
    this.viewport.innerHTML = "";
    const renderFn = this.routes[route];
    await renderFn(this.viewport, this);
  }
}

// Initialize Application on DOM Ready
window.addEventListener("DOMContentLoaded", () => {
  generateGrainTile();
  const viewport = document.getElementById("app-viewport");
  const router = new AppRouter(viewport);
  router.init();

  // Attach Nav Pill Click Handlers
  document.querySelectorAll(".nav-pill").forEach(pill => {
    pill.addEventListener("click", e => {
      e.preventDefault();
      const route = pill.getAttribute("data-route");
      router.navigate(route);
    });
  });
});
