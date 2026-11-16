/**
 * views/pages.js - Virtual Memory Page Replacement Studio
 * Reference Stream Editor | Frame Residency Timeline | Belady's Anomaly Sandbox
 */

import { API } from "../api.js";
import { createGlowCard } from "../glowcard.js";
import { showToast } from "../ui.js";

export async function renderPagesView(container) {
  let reference = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1];
  let frames = 3;
  let currentAlgorithm = "FIFO";
  let activeGlowCard = null;

  container.innerHTML = `
    <div class="pages-view-container" style="display: flex; flex-direction: column; gap: 24px;">
      <!-- Upper Controls & Glow Card -->
      <div style="display: grid; grid-template-columns: minmax(320px, 1.2fr) minmax(320px, 1fr); gap: 20px; align-items: start;">
        
        <!-- Column 1: Controls -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Page Replacement Controls</h2>
          
          <div class="form-group">
            <label class="form-label">Virtual Page Reference Stream</label>
            <input id="input-pages-reference" class="glass-input" type="text" value="${reference.join(', ')}">
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: center;">
            <div class="form-group" style="margin: 0;">
              <label class="form-label">Physical Frames</label>
              <input id="input-pages-frames" class="glass-input" type="number" min="1" max="100" value="${frames}">
            </div>
            <div style="display: flex; gap: 6px; margin-top: 18px;">
              <button id="btn-pages-sample" class="glass-btn glass-btn-sm" style="flex: 1;">Sample (20)</button>
              <button id="btn-pages-large" class="glass-btn glass-btn-sm" style="flex: 1;">Large (30)</button>
            </div>
          </div>

          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button id="btn-pages-run" class="glass-btn glass-btn-primary" style="flex: 1;">▶ Run</button>
            <button id="btn-pages-compare" class="glass-btn" style="flex: 1;">📊 Compare All</button>
            <button id="btn-pages-belady" class="glass-btn" style="flex: 1; border-color: rgba(251, 191, 36, 0.4); color: var(--warning);">⚡ Belady Anomaly</button>
          </div>
        </div>

        <!-- Column 2: Center Glow Card -->
        <div style="display: flex; justify-content: center;">
          <div id="pages-glow-card-target" style="width: 100%; display: flex; justify-content: center;"></div>
        </div>

      </div>

      <!-- Belady's Anomaly Highlight Panel -->
      <div id="belady-anomaly-panel" class="glass-panel-elevated" style="display: none; border-color: rgba(251, 191, 36, 0.35); flex-direction: column; gap: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 15px; font-weight: 600; color: var(--warning);">⚡ Belady's Anomaly Verification Sandbox</h3>
          <span class="brand-badge" style="background: rgba(251, 191, 36, 0.2); color: var(--warning);">NON-STACK ALGORITHM ANOMALY</span>
        </div>
        <div id="belady-comparison-body" style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;"></div>
        <p id="belady-explanation" style="font-size: 12px; color: var(--text-mid); line-height: 1.5; margin-top: 6px;"></p>
      </div>

      <!-- Step-by-Step Frame Residency Matrix -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Physical Frame Allocation Timeline</h3>
          <div style="display: flex; gap: 10px; font-size: 12px;">
            <span style="display: flex; align-items: center; gap: 4px;"><span style="display: inline-block; width: 10px; height: 10px; background: rgba(147, 207, 162, 0.6); border-radius: 2px;"></span> Hit</span>
            <span style="display: flex; align-items: center; gap: 4px;"><span style="display: inline-block; width: 10px; height: 10px; background: rgba(240, 138, 138, 0.6); border-radius: 2px;"></span> Page Fault</span>
          </div>
        </div>
        <div class="glass-table-wrapper" style="overflow-x: auto;">
          <table class="glass-table" id="pages-frame-table">
            <tbody id="pages-frame-tbody">
              <tr><td style="text-align: center; color: var(--text-dim); padding: 24px;">Run a simulation to view physical frame allocations.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Compare All Cards Row -->
      <div id="pages-compare-section" class="glass-panel" style="display: flex; flex-direction: column; gap: 16px;">
        <h3 style="font-size: 16px; font-weight: 600; color: #fff;">Algorithm Comparison (FIFO vs. LRU vs. Optimal)</h3>
        <div id="pages-compare-cards-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; justify-items: center;">
          <div style="color: var(--text-dim); padding: 14px;">Click 'Compare All' to benchmark fault ratios.</div>
        </div>
        <div id="pages-analysis-card" class="glass-panel-elevated" style="display: none; font-size: 13px; line-height: 1.6; color: var(--text-main);"></div>
      </div>
    </div>
  `;

  function setupPagesGlowCard(res) {
    const target = container.querySelector("#pages-glow-card-target");
    target.innerHTML = "";

    // Cumulative fault accumulation line
    let running = 0;
    const faultPoints = res ? res.steps.map(s => {
      if (s.is_fault) running++;
      return running;
    }) : [0];

    activeGlowCard = createGlowCard({
      container: target,
      title: "CUMULATIVE PAGE FAULTS",
      status: `${currentAlgorithm} · ${new Date().toLocaleTimeString()}`,
      value: res ? res.total_faults : 0,
      unit: "faults",
      caption: res ? `Hit ratio ${res.hit_ratio * 100:.1f}% (${res.total_hits} hits)` : "Awaiting execution",
      accent: "var(--accent-pages)",
      width: 340,
      points: faultPoints,
      optionsList: ["FIFO", "LRU", "Optimal"],
      selectedOption: currentAlgorithm,
      onOptionSelect: async opt => {
        currentAlgorithm = opt;
        await executeRun();
      }
    });
  }

  function renderFrameMatrix(res) {
    const tbody = container.querySelector("#pages-frame-tbody");
    tbody.innerHTML = "";

    // Row 1: Access Reference Page numbers
    const refTr = document.createElement("tr");
    refTr.style.background = "rgba(18, 32, 60, 0.6)";
    refTr.innerHTML = `<th style="position: sticky; left: 0; background: rgba(18, 32, 60, 0.9);">Page Access</th>` +
      res.steps.map(s => `<td style="text-align: center; font-weight: bold; color: #fff;">${s.page}</td>`).join("");
    tbody.appendChild(refTr);

    // Rows for each frame
    for (let f = 0; f < res.frames_count; f++) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<th style="position: sticky; left: 0; background: rgba(14, 24, 46, 0.9); color: var(--text-dim);">Frame ${f + 1}</th>` +
        res.steps.map(s => {
          const pageVal = s.frames[f] !== null && s.frames[f] !== undefined ? s.frames[f] : "-";
          const isCurrentAccess = s.frames[f] === s.page;
          const bg = isCurrentAccess ? (s.is_fault ? "rgba(240, 138, 138, 0.25)" : "rgba(147, 207, 162, 0.25)") : "transparent";
          return `<td style="text-align: center; background: ${bg};">${pageVal}</td>`;
        }).join("");
      tbody.appendChild(tr);
    }

    // Verdict Row: Hit or Fault
    const statTr = document.createElement("tr");
    statTr.innerHTML = `<th style="position: sticky; left: 0; background: rgba(18, 32, 60, 0.9);">Status</th>` +
      res.steps.map(s => {
        const text = s.is_fault ? "FAULT" : "HIT";
        const color = s.is_fault ? "var(--bad)" : "var(--good)";
        return `<td style="text-align: center; font-size: 11px; font-weight: bold; color: ${color};">${text}</td>`;
      }).join("");
    tbody.appendChild(statTr);
  }

  function syncInputs() {
    const refStr = container.querySelector("#input-pages-reference").value;
    frames = parseInt(container.querySelector("#input-pages-frames").value) || 3;
    reference = refStr.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));
  }

  async function executeRun() {
    syncInputs();
    try {
      const res = await API.runPages({
        reference,
        frames,
        algorithm: currentAlgorithm
      });

      if (!activeGlowCard) {
        setupPagesGlowCard(res);
      } else {
        let running = 0;
        const faultPoints = res.steps.map(s => {
          if (s.is_fault) running++;
          return running;
        });
        activeGlowCard.update({
          value: res.total_faults,
          caption: `Hit ratio ${(res.hit_ratio * 100).toFixed(1)}% (${res.total_hits} hits)`,
          status: `${res.algorithm} · ${new Date().toLocaleTimeString()}`,
          points: faultPoints
        });
      }

      renderFrameMatrix(res);
      showToast(`Executed ${currentAlgorithm}: ${res.total_faults} page faults`, "success");
    } catch (e) {
      // Error handled
    }
  }

  async function executeCompare() {
    syncInputs();
    try {
      showToast("Benchmarking page replacement algorithms...", "info");
      const comp = await API.comparePages({ reference, frames });

      const cardsRow = container.querySelector("#pages-compare-cards-row");
      cardsRow.innerHTML = "";

      for (const [alg, res] of Object.entries(comp.results)) {
        const isBest = comp.best_algorithms.includes(alg);
        const col = document.createElement("div");
        cardsRow.appendChild(col);

        createGlowCard({
          container: col,
          title: alg,
          status: isBest ? "★ FEWEST FAULTS" : "Evaluated",
          value: res.total_faults,
          unit: "faults",
          caption: `Hit: ${(res.hit_ratio * 100).toFixed(1)}% (${res.total_hits})`,
          accent: isBest ? "var(--accent-pages)" : "var(--accent-disk)",
          width: 200,
          points: [res.total_faults, res.total_hits]
        });
      }

      const card = container.querySelector("#pages-analysis-card");
      card.style.display = "block";
      card.innerHTML = comp.analysis.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
    } catch (e) {
      // Error handled
    }
  }

  async function executeBeladyDemo() {
    try {
      showToast("Evaluating Belady's Anomaly with benchmark sequence...", "info");
      const bel = await API.getBelady();
      const panel = container.querySelector("#belady-anomaly-panel");
      panel.style.display = "flex";

      const compBody = container.querySelector("#belady-comparison-body");
      compBody.innerHTML = `
        <div class="glass-panel" style="text-align: center;">
          <h4 style="color: var(--text-mid); font-size: 13px;">3 Page Frames (FIFO)</h4>
          <p style="font-size: 32px; font-weight: bold; color: var(--good); margin: 6px 0;">${bel.faults_3_frames} Faults</p>
          <span style="font-size: 11px; color: var(--text-dim);">Lower physical memory allocation</span>
        </div>
        <div class="glass-panel" style="text-align: center; border-color: rgba(240, 138, 138, 0.4);">
          <h4 style="color: var(--text-mid); font-size: 13px;">4 Page Frames (FIFO)</h4>
          <p style="font-size: 32px; font-weight: bold; color: var(--bad); margin: 6px 0;">${bel.faults_4_frames} Faults</p>
          <span style="font-size: 11px; color: var(--bad);">More memory resulted in MORE faults!</span>
        </div>
      `;
      container.querySelector("#belady-explanation").textContent = bel.explanation;
      panel.scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      // Error handled
    }
  }

  // Hook Events
  container.querySelector("#btn-pages-run").addEventListener("click", executeRun);
  container.querySelector("#btn-pages-compare").addEventListener("click", executeCompare);
  container.querySelector("#btn-pages-belady").addEventListener("click", executeBeladyDemo);

  container.querySelector("#btn-pages-sample").addEventListener("click", async () => {
    const s = await API.getSamples("pages");
    container.querySelector("#input-pages-reference").value = s.sample.reference.join(", ");
    container.querySelector("#input-pages-frames").value = s.sample.frames;
    await executeRun();
  });

  container.querySelector("#btn-pages-large").addEventListener("click", async () => {
    const s = await API.getSamples("pages");
    container.querySelector("#input-pages-reference").value = s.large.reference.join(", ");
    container.querySelector("#input-pages-frames").value = s.large.frames;
    await executeRun();
  });

  await executeRun();
}
