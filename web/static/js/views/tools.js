/**
 * views/tools.js - Platform Utilities, Diagnostics & Report Automation
 */

import { API } from "../api.js";
import { showToast } from "../ui.js";

export async function renderToolsView(container) {
  container.innerHTML = `
    <div class="tools-view-container" style="display: flex; flex-direction: column; gap: 24px;">
      <div>
        <h1 style="font-size: 24px; font-weight: 600; color: #fff;">Operating System Diagnostics & Reports</h1>
        <p style="color: var(--text-mid); font-size: 13px; margin-top: 4px;">
          Bash-integrated utilities for system telemetry, audit trail logging, and academic report compilation.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        <!-- Card 1: Academic Report Generator -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Academic Markdown Report</h2>
          <p style="font-size: 13px; color: var(--text-mid);">
            Synthesizes all 4 resource management modules into a publication-ready Markdown report complete with Matplotlib PNG figures.
          </p>
          <div style="display: flex; gap: 10px;">
            <button id="btn-tools-gen-large" class="glass-btn glass-btn-primary" style="flex: 1;">Generate (Large Dataset)</button>
            <button id="btn-tools-gen-sample" class="glass-btn" style="flex: 1;">Generate (Sample)</button>
          </div>
          <div id="tools-report-status" style="font-size: 12px; color: var(--text-dim);"></div>
        </div>

        <!-- Card 2: Test Verification Suite -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Automated Test Suite</h2>
          <p style="font-size: 13px; color: var(--text-mid);">
            Discovers and executes all unit and API verification assertions via <code>run_tests.sh</code>.
          </p>
          <button id="btn-tools-run-tests" class="glass-btn glass-btn-primary">▶ Execute Test Discovery</button>
          <div id="tools-test-status" style="font-size: 12px; color: var(--text-dim);"></div>
        </div>

        <!-- Card 3: Host Telemetry -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Host Telemetry (sysinfo.sh)</h2>
          <p style="font-size: 13px; color: var(--text-mid);">
            Inspect live Linux kernel parameters, memory usage, CPU topology, and real system scheduler processes.
          </p>
          <button id="btn-tools-refresh-sysinfo" class="glass-btn">🔄 Refresh Host Telemetry</button>
        </div>

        <!-- Card 4: Audit Log Aggregator -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Activity Log Summary (collect_logs.sh)</h2>
          <p style="font-size: 13px; color: var(--text-mid);">
            Audits activity records, module frequencies, and error logs recorded under <code>logs/activity.log</code>.
          </p>
          <button id="btn-tools-refresh-logs" class="glass-btn">📋 Refresh Log Audit</button>
        </div>
      </div>

      <!-- Output Display Console -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 id="tools-console-title" style="font-size: 15px; font-weight: 600; color: #fff;">Terminal Output Console</h3>
          <button id="btn-tools-clear-console" class="glass-btn glass-btn-sm">Clear</button>
        </div>
        <pre id="tools-console-body" class="glass-textarea" style="width: 100%; height: 380px; padding: 14px; overflow: auto; font-size: 12px; border-radius: 12px;">Select an automated tool above to view live execution logs and outputs.</pre>
      </div>
    </div>
  `;

  const consoleTitle = container.querySelector("#tools-console-title");
  const consoleBody = container.querySelector("#tools-console-body");

  container.querySelector("#btn-tools-gen-large").addEventListener("click", async () => {
    showToast("Generating full report on large dataset...", "info");
    consoleTitle.textContent = "Report Generator Output";
    consoleBody.textContent = "Synthesizing benchmarks and rendering PNG figures...";
    try {
      const rep = await API.generateReport({ dataset: "large" });
      container.querySelector("#tools-report-status").textContent = `Saved to: ${rep.report_path}`;
      consoleBody.textContent = rep.markdown;
      showToast("Report generated successfully!", "success");
    } catch (e) {
      consoleBody.textContent = "Report generation failed.";
    }
  });

  container.querySelector("#btn-tools-gen-sample").addEventListener("click", async () => {
    showToast("Generating full report on sample benchmark...", "info");
    consoleTitle.textContent = "Report Generator Output (Sample)";
    consoleBody.textContent = "Synthesizing benchmarks...";
    try {
      const rep = await API.generateReport({ dataset: "sample" });
      container.querySelector("#tools-report-status").textContent = `Saved to: ${rep.report_path}`;
      consoleBody.textContent = rep.markdown;
      showToast("Report generated successfully!", "success");
    } catch (e) {
      consoleBody.textContent = "Report generation failed.";
    }
  });

  container.querySelector("#btn-tools-run-tests").addEventListener("click", async () => {
    showToast("Executing automated test discovery suite...", "info");
    consoleTitle.textContent = "Test Discovery Console (run_tests.sh)";
    consoleBody.textContent = "Discovering and running unittest suites...";
    try {
      const res = await API.runTests();
      const statusLabel = container.querySelector("#tools-test-status");
      statusLabel.innerHTML = res.passed ? `<span style="color: var(--good); font-weight: bold;">✓ ALL TESTS PASSED</span>` : `<span style="color: var(--bad); font-weight: bold;">✕ TEST FAILURES DETECTED</span>`;
      consoleBody.textContent = res.stdout;
      showToast(res.passed ? "All tests passed!" : "Tests finished with failures.", res.passed ? "success" : "error");
    } catch (e) {
      consoleBody.textContent = "Test execution failed.";
    }
  });

  container.querySelector("#btn-tools-refresh-sysinfo").addEventListener("click", async () => {
    consoleTitle.textContent = "Host System Diagnostics (sysinfo.sh)";
    consoleBody.textContent = "Gathering Linux kernel, CPU, and memory metrics...";
    try {
      const res = await API.getSysinfo();
      consoleBody.textContent = res.stdout;
    } catch (e) {
      consoleBody.textContent = "Failed to fetch system info.";
    }
  });

  container.querySelector("#btn-tools-refresh-logs").addEventListener("click", async () => {
    consoleTitle.textContent = "Audit Log Summary (collect_logs.sh)";
    consoleBody.textContent = "Aggregating activity log statistics...";
    try {
      const res = await API.getLogsSummary();
      consoleBody.textContent = res.stdout;
    } catch (e) {
      consoleBody.textContent = "Failed to fetch log summary.";
    }
  });

  container.querySelector("#btn-tools-clear-console").addEventListener("click", () => {
    consoleBody.textContent = "Console cleared.";
  });
}
