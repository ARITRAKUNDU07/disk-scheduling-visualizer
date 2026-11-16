/**
 * views/cpu.js - CPU Scheduling Studio
 * Process Table Editor | Native Canvas Gantt Chart | Process Metrics | Multi-Algorithm Compare
 */

import { API } from "../api.js";
import { renderCPUGantt } from "../charts.js";
import { createGlowCard } from "../glowcard.js";
import { showToast } from "../ui.js";

export async function renderCPUView(container) {
  let processes = [
    { pid: "P1", arrival: 0, burst: 24, priority: 3 },
    { pid: "P2", arrival: 0, burst: 3, priority: 1 },
    { pid: "P3", arrival: 0, burst: 3, priority: 2 }
  ];
  let currentAlgorithm = "FCFS";
  let currentQuantum = 4.0;
  let activeGlowCard = null;

  container.innerHTML = `
    <div class="cpu-view-container" style="display: flex; flex-direction: column; gap: 24px;">
      <!-- Top Grid: Process Console | Glow Card -->
      <div style="display: grid; grid-template-columns: minmax(320px, 1.2fr) minmax(320px, 1fr); gap: 20px; align-items: start;">
        
        <!-- Column 1: Process Table Console -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Process Configuration</h2>
            <div style="display: flex; gap: 6px;">
              <button id="btn-add-process" class="glass-btn glass-btn-sm">+ Add Row</button>
              <button id="btn-load-sample-cpu" class="glass-btn glass-btn-sm">Sample</button>
              <button id="btn-load-large-cpu" class="glass-btn glass-btn-sm">Large (12)</button>
            </div>
          </div>

          <div class="glass-table-wrapper" style="max-height: 250px; overflow-y: auto;">
            <table class="glass-table">
              <thead>
                <tr>
                  <th>PID</th>
                  <th>Arrival</th>
                  <th>Burst</th>
                  <th>Priority</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody id="cpu-process-tbody"></tbody>
            </table>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: center; margin-top: 6px;">
            <div class="form-group" style="margin: 0;">
              <label class="form-label">Round Robin Quantum</label>
              <input id="input-cpu-quantum" class="glass-input" type="number" step="1" min="1" value="${currentQuantum}">
            </div>
            <div style="display: flex; gap: 8px; margin-top: 18px;">
              <button id="btn-run-cpu" class="glass-btn glass-btn-primary" style="flex: 1;">▶ Run</button>
              <button id="btn-compare-cpu" class="glass-btn" style="flex: 1;">📊 Compare</button>
            </div>
          </div>
        </div>

        <!-- Column 2: Centerpiece Glow Card -->
        <div style="display: flex; justify-content: center;">
          <div id="cpu-glow-card-target" style="width: 100%; display: flex; justify-content: center;"></div>
        </div>

      </div>

      <!-- Gantt Chart Canvas Panel -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Visual Execution Timeline (Gantt Chart)</h3>
          <span id="gantt-summary-label" style="font-size: 12px; color: var(--text-mid);"></span>
        </div>
        <canvas id="cpu-gantt-canvas" style="width: 100%; height: 140px;"></canvas>
      </div>

      <!-- Process Metrics Breakdown Table -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 12px;">
        <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Scheduling Metrics Matrix</h3>
        <div class="glass-table-wrapper">
          <table class="glass-table">
            <thead>
              <tr>
                <th>PID</th>
                <th>Arrival</th>
                <th>Burst</th>
                <th>Priority</th>
                <th>Completion</th>
                <th>Turnaround</th>
                <th>Waiting</th>
                <th>Response</th>
              </tr>
            </thead>
            <tbody id="cpu-metrics-tbody">
              <tr><td colspan="8" style="text-align: center; color: var(--text-dim);">Run an algorithm to inspect latency metrics.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Compare All CPU Cards -->
      <div id="cpu-compare-section" class="glass-panel" style="display: flex; flex-direction: column; gap: 16px;">
        <h3 style="font-size: 16px; font-weight: 600; color: #fff;">Multi-Algorithm Comparative Evaluation</h3>
        <div id="cpu-compare-cards-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; justify-items: center;">
          <div style="color: var(--text-dim); padding: 14px;">Click 'Compare' to evaluate all 5 CPU algorithms simultaneously.</div>
        </div>
        <div id="cpu-analysis-card" class="glass-panel-elevated" style="display: none; font-size: 13px; line-height: 1.6; color: var(--text-main);"></div>
      </div>
    </div>
  `;

  function renderProcessTable() {
    const tbody = container.querySelector("#cpu-process-tbody");
    tbody.innerHTML = "";

    processes.forEach((p, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input type="text" class="glass-input" style="width: 60px; padding: 4px 6px;" value="${p.pid}" data-idx="${idx}" data-field="pid"></td>
        <td><input type="number" class="glass-input" style="width: 60px; padding: 4px 6px;" value="${p.arrival}" data-idx="${idx}" data-field="arrival"></td>
        <td><input type="number" class="glass-input" style="width: 60px; padding: 4px 6px;" value="${p.burst}" data-idx="${idx}" data-field="burst"></td>
        <td><input type="number" class="glass-input" style="width: 60px; padding: 4px 6px;" value="${p.priority || 0}" data-idx="${idx}" data-field="priority"></td>
        <td><button class="glass-btn glass-btn-sm" style="color: var(--bad); padding: 2px 8px;" data-del="${idx}">✕</button></td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("input").forEach(inp => {
      inp.addEventListener("change", e => {
        const idx = parseInt(e.target.dataset.idx);
        const fld = e.target.dataset.field;
        processes[idx][fld] = fld === "pid" ? e.target.value : parseFloat(e.target.value) || 0;
      });
    });

    tbody.querySelectorAll("button[data-del]").forEach(btn => {
      btn.addEventListener("click", e => {
        const idx = parseInt(e.target.dataset.del);
        if (processes.length > 1) {
          processes.splice(idx, 1);
          renderProcessTable();
        } else {
          showToast("At least one process is required.", "warning");
        }
      });
    });
  }

  function setupCPUGlowCard(res) {
    const target = container.querySelector("#cpu-glow-card-target");
    target.innerHTML = "";

    const waitingPoints = res ? res.process_metrics.map(m => m.waiting) : [0];

    activeGlowCard = createGlowCard({
      container: target,
      title: "AVG WAITING LATENCY",
      status: `${currentAlgorithm} · ${new Date().toLocaleTimeString()}`,
      value: res ? res.avg_waiting : 0,
      unit: "units",
      caption: res ? `Turnaround ${res.avg_turnaround} · Util ${res.cpu_utilization}%` : "Awaiting execution",
      accent: "var(--accent-cpu)",
      width: 340,
      points: waitingPoints,
      optionsList: ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"],
      selectedOption: currentAlgorithm,
      onOptionSelect: async opt => {
        currentAlgorithm = opt;
        await executeRun();
      }
    });
  }

  async function executeRun() {
    currentQuantum = parseFloat(container.querySelector("#input-cpu-quantum").value) || 4.0;
    try {
      const res = await API.runCPU({
        processes,
        algorithm: currentAlgorithm,
        quantum: currentQuantum
      });

      if (!activeGlowCard) {
        setupCPUGlowCard(res);
      } else {
        activeGlowCard.update({
          value: res.avg_waiting,
          caption: `Turnaround ${res.avg_turnaround} · Util ${res.cpu_utilization}%`,
          status: `${res.algorithm} · ${new Date().toLocaleTimeString()}`,
          points: res.process_metrics.map(m => m.waiting)
        });
      }

      // Render Gantt
      const canvas = container.querySelector("#cpu-gantt-canvas");
      renderCPUGantt(canvas, res.gantt);
      container.querySelector("#gantt-summary-label").textContent = `${res.algorithm} Timeline: Throughput ${res.throughput} proc/unit`;

      // Render Metrics Table
      const mbody = container.querySelector("#cpu-metrics-tbody");
      mbody.innerHTML = "";
      res.process_metrics.forEach(m => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${m.pid}</strong></td>
          <td>${m.arrival}</td>
          <td>${m.burst}</td>
          <td>${m.priority}</td>
          <td>${m.completion}</td>
          <td>${m.turnaround}</td>
          <td style="color: var(--accent-cpu); font-weight: 600;">${m.waiting}</td>
          <td>${m.response}</td>
        `;
        mbody.appendChild(tr);
      });

      showToast(`Executed ${currentAlgorithm}: Avg Waiting ${res.avg_waiting}`, "success");
    } catch (e) {
      // Error handled
    }
  }

  async function executeCompare() {
    currentQuantum = parseFloat(container.querySelector("#input-cpu-quantum").value) || 4.0;
    try {
      showToast("Benchmarking all CPU scheduling algorithms...", "info");
      const comp = await API.compareCPU({ processes, quantum: currentQuantum });

      const cardsRow = container.querySelector("#cpu-compare-cards-row");
      cardsRow.innerHTML = "";

      for (const [alg, res] of Object.entries(comp.results)) {
        const isBest = comp.best_algorithms.includes(alg);
        const col = document.createElement("div");
        cardsRow.appendChild(col);

        createGlowCard({
          container: col,
          title: alg,
          status: isBest ? "★ OPTIMAL" : "Evaluated",
          value: res.avg_waiting,
          unit: "units",
          caption: `Turnaround: ${res.avg_turnaround}`,
          accent: isBest ? "var(--accent-pages)" : "var(--accent-cpu)",
          width: 175,
          points: res.process_metrics.map(m => m.waiting)
        });
      }

      const card = container.querySelector("#cpu-analysis-card");
      card.style.display = "block";
      card.innerHTML = comp.analysis.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
    } catch (e) {
      // Error handled
    }
  }

  // Hook Event Handlers
  container.querySelector("#btn-add-process").addEventListener("click", () => {
    const nextPid = `P${processes.length + 1}`;
    processes.push({ pid: nextPid, arrival: 0, burst: 4, priority: 1 });
    renderProcessTable();
  });

  container.querySelector("#btn-load-sample-cpu").addEventListener("click", async () => {
    const s = await API.getSamples("cpu");
    processes = s.sample.processes;
    container.querySelector("#input-cpu-quantum").value = s.sample.quantum || 4.0;
    renderProcessTable();
    await executeRun();
  });

  container.querySelector("#btn-load-large-cpu").addEventListener("click", async () => {
    const s = await API.getSamples("cpu");
    processes = s.large.processes;
    container.querySelector("#input-cpu-quantum").value = s.large.quantum || 5.0;
    renderProcessTable();
    await executeRun();
  });

  container.querySelector("#btn-run-cpu").addEventListener("click", executeRun);
  container.querySelector("#btn-compare-cpu").addEventListener("click", executeCompare);

  renderProcessTable();
  await executeRun();
}
