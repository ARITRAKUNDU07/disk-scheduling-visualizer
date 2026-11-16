/**
 * views/dashboard.js - Executive Overview with 4 Interactive Glow Cards
 */

import { API } from "../api.js";
import { createGlowCard } from "../glowcard.js";
import { openDrawer, showToast } from "../ui.js";

export async function renderDashboard(container, router) {
  container.innerHTML = `
    <div class="dashboard-view" style="display: flex; flex-direction: column; gap: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
          <h1 style="font-size: 24px; font-weight: 600; color: #fff;">System Overview & Telemetry</h1>
          <p style="color: var(--text-mid); font-size: 13px; margin-top: 4px;">
            Real-time optimal algorithmic metrics synthesized across operating system resource managers.
          </p>
        </div>
        <div style="font-size: 12px; color: var(--text-dim);" id="dashboard-refresh-time">
          Updated: Live
        </div>
      </div>

      <!-- 4 Responsive Glow Cards Grid -->
      <div id="dashboard-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; justify-items: center;">
        <div class="glass-panel" style="width: 100%; text-align: center; padding: 40px; color: var(--text-mid);">
          Synthesizing live subsystem benchmarks...
        </div>
      </div>

      <!-- Bottom Glass Action Bar -->
      <div class="glass-panel" style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; padding: 14px 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-weight: 600; font-size: 13px; color: #fff;">Platform Utilities:</span>
          <span style="color: var(--text-dim); font-size: 12px;">Automated OS diagnostics and verification suites</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          <button id="btn-full-analysis" class="glass-btn glass-btn-primary">⚡ Full Analysis</button>
          <button id="btn-gen-report" class="glass-btn">📄 Generate Report</button>
          <button id="btn-audit-log" class="glass-btn">📋 Activity Log</button>
          <button id="btn-sysinfo" class="glass-btn">🖥 System Info</button>
          <button id="btn-run-tests" class="glass-btn">🧪 Run Tests</button>
        </div>
      </div>
    </div>
  `;

  // Fetch summary metrics
  try {
    const summary = await API.getSummary();
    const grid = container.querySelector("#dashboard-cards-grid");
    grid.innerHTML = "";

    // 1. Disk Glow Card
    const diskWrap = document.createElement("div");
    diskWrap.style.cursor = "pointer";
    diskWrap.title = "Click to inspect Disk Scheduling Studio";
    diskWrap.addEventListener("click", () => router.navigate("disk"));
    grid.appendChild(diskWrap);

    createGlowCard({
      container: diskWrap,
      title: "DISK HEAD TRAVEL",
      status: `Best: ${summary.disk.best_algorithm}`,
      value: summary.disk.headline_value,
      unit: "cyl",
      caption: summary.disk.caption,
      accent: "var(--accent-disk)",
      width: 270,
      points: summary.disk.sequence,
    });

    // 2. CPU Glow Card
    const cpuWrap = document.createElement("div");
    cpuWrap.style.cursor = "pointer";
    cpuWrap.title = "Click to inspect CPU Scheduling Studio";
    cpuWrap.addEventListener("click", () => router.navigate("cpu"));
    grid.appendChild(cpuWrap);

    createGlowCard({
      container: cpuWrap,
      title: "CPU AVG WAITING",
      status: `Best: ${summary.cpu.best_algorithm}`,
      value: summary.cpu.headline_value,
      unit: "units",
      caption: summary.cpu.caption,
      accent: "var(--accent-cpu)",
      width: 270,
      points: [17, 10, 5.67, 3.0, 7.5],
    });

    // 3. Page Replacement Glow Card
    const pageWrap = document.createElement("div");
    pageWrap.style.cursor = "pointer";
    pageWrap.title = "Click to inspect Page Replacement Studio";
    pageWrap.addEventListener("click", () => router.navigate("pages"));
    grid.appendChild(pageWrap);

    createGlowCard({
      container: pageWrap,
      title: "PAGE FAULT MINIMA",
      status: `Best: ${summary.pages.best_algorithm}`,
      value: summary.pages.headline_value,
      unit: "faults",
      caption: summary.pages.caption,
      accent: "var(--accent-pages)",
      width: 270,
      points: [15, 12, 9],
      trend: "down",
    });

    // 4. Deadlock Glow Card
    const dlWrap = document.createElement("div");
    dlWrap.style.cursor = "pointer";
    dlWrap.title = "Click to inspect Deadlock Studio";
    dlWrap.addEventListener("click", () => router.navigate("deadlock"));
    grid.appendChild(dlWrap);

    createGlowCard({
      container: dlWrap,
      title: "DEADLOCK SAFETY",
      status: "Banker's Test",
      value: summary.deadlock.headline_value,
      unit: "state",
      caption: summary.deadlock.caption,
      accent: summary.deadlock.is_safe ? "var(--accent-deadlock)" : "var(--accent-unsafe)",
      width: 270,
      points: summary.deadlock.available,
    });

    container.querySelector("#dashboard-refresh-time").textContent = `Updated: ${new Date().toLocaleTimeString()}`;

  } catch (err) {
    showToast("Failed to load dashboard summary metrics.", "error");
  }

  // Hook Action Bar Buttons
  container.querySelector("#btn-full-analysis").addEventListener("click", async () => {
    showToast("Synthesizing full multi-module analytical benchmark...", "info");
    const summary = await API.getSummary();
    const content = document.createElement("div");
    content.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div class="glass-panel">
          <h3 style="color: var(--accent-disk); margin-bottom: 8px;">1. Disk Scheduling</h3>
          <p>Optimal: <strong>${summary.disk.best_algorithm}</strong> with ${summary.disk.headline_value} cylinders traveled.</p>
          <p style="font-size: 12px; color: var(--text-mid); margin-top: 4px;">${summary.disk.caption}</p>
        </div>
        <div class="glass-panel">
          <h3 style="color: var(--accent-cpu); margin-bottom: 8px;">2. CPU Scheduling</h3>
          <p>Optimal: <strong>${summary.cpu.best_algorithm}</strong> with average waiting time of ${summary.cpu.headline_value} time units.</p>
          <p style="font-size: 12px; color: var(--text-mid); margin-top: 4px;">${summary.cpu.caption}</p>
        </div>
        <div class="glass-panel">
          <h3 style="color: var(--accent-pages); margin-bottom: 8px;">3. Page Replacement</h3>
          <p>Optimal: <strong>${summary.pages.best_algorithm}</strong> incurring only ${summary.pages.headline_value} page faults.</p>
          <p style="font-size: 12px; color: var(--text-mid); margin-top: 4px;">${summary.pages.caption}</p>
        </div>
        <div class="glass-panel">
          <h3 style="color: var(--accent-deadlock); margin-bottom: 8px;">4. Deadlock Avoidance</h3>
          <p>Status: <strong style="color: ${summary.deadlock.is_safe ? 'var(--good)' : 'var(--bad)'}">${summary.deadlock.headline_value}</strong></p>
          <p style="font-size: 12px; color: var(--text-mid); margin-top: 4px;">${summary.deadlock.caption}</p>
        </div>
      </div>
    `;
    openDrawer("Comprehensive Multi-Subsystem Analysis", content);
  });

  container.querySelector("#btn-gen-report").addEventListener("click", async () => {
    showToast("Generating comprehensive Markdown report and Matplotlib charts...", "info");
    try {
      const rep = await API.generateReport({ dataset: "large" });
      const content = document.createElement("div");
      content.innerHTML = `
        <div style="margin-bottom: 14px;">
          <p style="color: var(--good); font-weight: 600;">✓ Report Generated Successfully</p>
          <p style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">Saved to: <code>${rep.report_path}</code></p>
        </div>
        <pre class="glass-textarea" style="width: 100%; height: 500px; padding: 14px; overflow: auto; font-size: 12px; border-radius: 12px;">${rep.markdown.replace(/</g, "&lt;")}</pre>
      `;
      openDrawer("Generated Laboratory Report Preview", content);
    } catch (err) {
      showToast("Report generation failed.", "error");
    }
  });

  container.querySelector("#btn-audit-log").addEventListener("click", async () => {
    try {
      const res = await API.getLogsSummary();
      const content = document.createElement("pre");
      content.className = "glass-panel";
      content.style.fontFamily = "var(--font-mono)";
      content.style.fontSize = "12px";
      content.style.whiteSpace = "pre-wrap";
      content.textContent = res.stdout || "Log file empty.";
      openDrawer("Activity Audit Log Summary (collect_logs.sh)", content);
    } catch (e) {
      showToast("Failed to fetch log summary.", "error");
    }
  });

  container.querySelector("#btn-sysinfo").addEventListener("click", async () => {
    try {
      const res = await API.getSysinfo();
      const content = document.createElement("pre");
      content.className = "glass-panel";
      content.style.fontFamily = "var(--font-mono)";
      content.style.fontSize = "12px";
      content.style.whiteSpace = "pre-wrap";
      content.textContent = res.stdout || "System information unavailable.";
      openDrawer("Host System Diagnostics (sysinfo.sh)", content);
    } catch (e) {
      showToast("Failed to fetch system information.", "error");
    }
  });

  container.querySelector("#btn-run-tests").addEventListener("click", async () => {
    showToast("Executing automated test discovery suite...", "info");
    try {
      const res = await API.runTests();
      const content = document.createElement("div");
      content.innerHTML = `
        <div style="margin-bottom: 12px;">
          <span class="brand-badge" style="background: ${res.passed ? 'rgba(147, 207, 162, 0.2)' : 'rgba(240, 138, 138, 0.2)'}; color: ${res.passed ? 'var(--good)' : 'var(--bad)'}; font-size: 13px;">
            ${res.passed ? 'PASSED ALL ASSERTIONS' : 'TESTS FAILED'}
          </span>
        </div>
        <pre class="glass-panel" style="font-family: var(--font-mono); font-size: 12px; white-space: pre-wrap; max-height: 500px; overflow: auto;">${res.stdout}</pre>
      `;
      openDrawer("Automated Verification Suite (run_tests.sh)", content);
    } catch (e) {
      showToast("Test execution failed.", "error");
    }
  });
}
