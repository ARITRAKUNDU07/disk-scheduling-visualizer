/**
 * views/disk.js - Flagship Disk Head Scheduling Studio
 * Full 3-column layout: Control Panel | Large Glow Card | Step Trace
 * Followed by Compare All 6 Glow Cards and Classical Space-Time Canvas.
 */

import { API } from "../api.js";
import { renderClassicalDiskChart } from "../charts.js";
import { createGlowCard } from "../glowcard.js";
import { createSegmentedControl, showToast } from "../ui.js";

export async function renderDiskView(container) {
  let diskMeta = null;
  try {
    const meta = await API.getMeta();
    diskMeta = meta.modules.disk;
  } catch (e) {
    diskMeta = {
      algorithms: ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"],
      default_algorithm: "FCFS"
    };
  }

  // Initial Parameters (Benchmark)
  let currentParams = {
    requests: [98, 183, 37, 122, 14, 124, 65, 67],
    head: 53,
    size: 200,
    direction: "left",
    algorithm: "FCFS",
    count_jump: true,
    ms_per_cyl: 1.0,
  };

  let activeResult = null;
  let activeGlowCard = null;
  let playbackStep = 0;
  let playbackInterval = null;
  let runCounter = 1;
  let isClassicView = false;

  container.innerHTML = `
    <div class="disk-view-container" style="display: flex; flex-direction: column; gap: 24px;">
      <!-- Main Upper Stage: Controls | Main Card | Trace Log -->
      <div style="display: grid; grid-template-columns: minmax(280px, 1fr) minmax(360px, 1.3fr) minmax(300px, 1.1fr); gap: 20px; align-items: start;">
        
        <!-- Column 1: Control Console -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <h2 style="font-size: 16px; font-weight: 600; color: #fff;">Disk Head Controls</h2>
          
          <div class="form-group">
            <label class="form-label">Cylinder Request Queue</label>
            <input id="input-disk-queue" class="glass-input" type="text" value="${currentParams.requests.join(', ')}">
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div class="form-group">
              <label class="form-label">Head (0..N-1)</label>
              <input id="input-disk-head" class="glass-input" type="number" value="${currentParams.head}">
            </div>
            <div class="form-group">
              <label class="form-label">Total Cylinders</label>
              <input id="input-disk-size" class="glass-input" type="number" value="${currentParams.size}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; align-items: center;">
            <div class="form-group">
              <label class="form-label">Initial Direction</label>
              <div id="disk-dir-segmented"></div>
            </div>
            <div class="form-group">
              <label class="form-label">Seek Delay (ms/cyl)</label>
              <input id="input-disk-rate" class="glass-input" type="number" step="0.1" value="${currentParams.ms_per_cyl}">
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 0;">
            <span style="font-size: 13px; color: var(--text-mid);">Count Return Jump (C-SCAN/C-LOOK)</span>
            <input id="input-disk-count-jump" type="checkbox" ${currentParams.count_jump ? 'checked' : ''} style="cursor: pointer; width: 18px; height: 18px;">
          </div>

          <!-- Action Buttons -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 6px;">
            <button id="btn-disk-run" class="glass-btn glass-btn-primary">▶ Run</button>
            <button id="btn-disk-compare" class="glass-btn">📊 Compare All</button>
            <button id="btn-disk-play" class="glass-btn">⏯ Playback</button>
            <button id="btn-disk-step" class="glass-btn">⏭ Step</button>
            <button id="btn-disk-sample" class="glass-btn">Sample Data</button>
            <button id="btn-disk-large" class="glass-btn">Large Data</button>
            <button id="btn-disk-random" class="glass-btn">🎲 Random</button>
            <button id="btn-disk-toggle-view" class="glass-btn">🔄 Space-Time</button>
          </div>
        </div>

        <!-- Column 2: Large Centerpiece Glow Card -->
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
          <div id="main-glow-card-target" style="width: 100%; display: flex; justify-content: center;"></div>
        </div>

        <!-- Column 3: Step-by-Step Trace Log -->
        <div class="glass-panel" style="display: flex; flex-direction: column; height: 500px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Head Movement Trace</h3>
            <span id="disk-trace-summary" style="font-size: 12px; color: var(--text-mid);">0 steps</span>
          </div>
          <div id="disk-trace-table-container" style="flex: 1; overflow-y: auto;">
            <table class="glass-table">
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Path</th>
                  <th>Dist</th>
                  <th>Running Total</th>
                </tr>
              </thead>
              <tbody id="disk-trace-tbody">
                <tr><td colspan="4" style="text-align: center; color: var(--text-dim);">Execute simulation to view step transitions.</td></tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- Classical Space-Time View (Collapsible) -->
      <div id="disk-classical-container" class="glass-panel" style="display: none; flex-direction: column; gap: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Classical Cylinder Space-Time Diagram (x = Cylinder, y = Time ↓)</h3>
          <span style="font-size: 12px; color: var(--text-dim);">Physical arm traversal path</span>
        </div>
        <canvas id="disk-classical-canvas" style="width: 100%; height: 320px;"></canvas>
      </div>

      <!-- Compare All 6 Algorithms Section -->
      <div id="disk-compare-section" class="glass-panel" style="display: flex; flex-direction: column; gap: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 16px; font-weight: 600; color: #fff;">Algorithm Comparison Matrix (All 6 Solvers)</h3>
          <span id="disk-best-badge" class="brand-badge" style="display: none;"></span>
        </div>
        
        <div id="disk-compare-cards-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; justify-items: center;">
          <div style="color: var(--text-dim); padding: 20px;">Click 'Compare All' to generate concurrent multi-algorithm benchmark cards.</div>
        </div>

        <div id="disk-analysis-card" class="glass-panel-elevated" style="display: none; font-size: 13px; line-height: 1.6; color: var(--text-main);">
        </div>
      </div>
    </div>
  `;

  // Setup Direction Segmented Control
  createSegmentedControl({
    container: container.querySelector("#disk-dir-segmented"),
    options: [
      { label: "Left ←", value: "left" },
      { label: "Right →", value: "right" }
    ],
    selected: currentParams.direction,
    onSelect: val => {
      currentParams.direction = val;
    }
  });

  // Render Initial Center Glow Card
  function setupMainGlowCard(res) {
    const target = container.querySelector("#main-glow-card-target");
    target.innerHTML = "";

    activeGlowCard = createGlowCard({
      container: target,
      title: "CYLINDER HEAD TRAJECTORY",
      status: `Run #${runCounter++} · ${new Date().toLocaleTimeString()}`,
      value: res ? res.total_movement : 0,
      unit: "cyl",
      caption: res ? `Avg seek ${res.avg_seek} · Seek delay ${res.seek_time_ms} ms` : "Awaiting execution",
      accent: "var(--accent-disk)",
      width: 360,
      points: res ? res.sequence : currentParams.requests,
      optionsList: diskMeta.algorithms,
      selectedOption: currentParams.algorithm,
      isStraight: true,
      onOptionSelect: async opt => {
        currentParams.algorithm = opt;
        await executeRun();
      }
    });
  }

  // Populate Trace Table
  function populateTraceTable(steps) {
    const tbody = container.querySelector("#disk-trace-tbody");
    tbody.innerHTML = "";
    container.querySelector("#disk-trace-summary").textContent = `${steps.length} cylinder steps`;

    steps.forEach((st, idx) => {
      const tr = document.createElement("tr");
      tr.id = `disk-trace-row-${idx}`;
      const jumpTag = st.is_jump ? ` <span style="color: var(--jump); font-weight: bold;">[JUMP]</span>` : "";
      tr.innerHTML = `
        <td style="font-weight: 600;">${st.step}</td>
        <td>${st.from_cyl} → ${st.to_cyl}${jumpTag}</td>
        <td>${st.distance}</td>
        <td style="color: var(--text-mid);">${st.cumulative}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Read Inputs from Console
  function syncInputs() {
    const qStr = container.querySelector("#input-disk-queue").value;
    const hVal = parseInt(container.querySelector("#input-disk-head").value);
    const sVal = parseInt(container.querySelector("#input-disk-size").value);
    const msVal = parseFloat(container.querySelector("#input-disk-rate").value);
    const jVal = container.querySelector("#input-disk-count-jump").checked;

    const reqs = qStr.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));

    currentParams.requests = reqs;
    currentParams.head = hVal;
    currentParams.size = sVal;
    currentParams.ms_per_cyl = msVal;
    currentParams.count_jump = jVal;
  }

  // Execute Single Algorithm Run
  async function executeRun() {
    syncInputs();
    try {
      const res = await API.runDisk(currentParams);
      activeResult = res;

      if (!activeGlowCard) {
        setupMainGlowCard(res);
      } else {
        activeGlowCard.update({
          value: res.total_movement,
          caption: `Avg seek ${res.avg_seek} · Seek delay ${res.seek_time_ms} ms`,
          status: `${res.algorithm} · ${new Date().toLocaleTimeString()}`,
          points: res.sequence
        });
      }

      populateTraceTable(res.steps);

      if (isClassicView) {
        const canvas = container.querySelector("#disk-classical-canvas");
        renderClassicalDiskChart(canvas, res.steps, currentParams.size);
      }

      showToast(`Executed ${currentParams.algorithm}: ${res.total_movement} cylinders`, "success");
    } catch (err) {
      // Error handled by API toast
    }
  }

  // Execute Compare All
  async function executeCompare() {
    syncInputs();
    try {
      showToast("Benchmarking all 6 disk algorithms concurrently...", "info");
      const comp = await API.compareDisk(currentParams);

      const cardsRow = container.querySelector("#disk-compare-cards-row");
      cardsRow.innerHTML = "";

      const bestBadge = container.querySelector("#disk-best-badge");
      bestBadge.style.display = "inline-block";
      bestBadge.textContent = `OPTIMAL: ${comp.best_algorithms.join(', ')} (${comp.best_movement} cyl)`;
      bestBadge.style.background = "rgba(147, 207, 162, 0.2)";
      bestBadge.style.color = "var(--good)";

      for (const [alg, res] of Object.entries(comp.results)) {
        const isBest = comp.best_algorithms.includes(alg);
        const cardCol = document.createElement("div");
        cardsRow.appendChild(cardCol);

        createGlowCard({
          container: cardCol,
          title: alg,
          status: isBest ? "★ WINNER" : "Evaluated",
          value: res.total_movement,
          unit: "cyl",
          caption: `Seek: ${res.seek_time_ms} ms`,
          accent: isBest ? "var(--accent-pages)" : "var(--accent-disk)",
          width: 175,
          points: res.sequence,
        });
      }

      const analysisCard = container.querySelector("#disk-analysis-card");
      analysisCard.style.display = "block";
      analysisCard.innerHTML = comp.analysis.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");

    } catch (err) {
      // Error handled
    }
  }

  // Event Listeners
  container.querySelector("#btn-disk-run").addEventListener("click", executeRun);
  container.querySelector("#btn-disk-compare").addEventListener("click", executeCompare);

  container.querySelector("#btn-disk-sample").addEventListener("click", async () => {
    const s = await API.getSamples("disk");
    container.querySelector("#input-disk-queue").value = s.sample.requests.join(", ");
    container.querySelector("#input-disk-head").value = s.sample.head;
    container.querySelector("#input-disk-size").value = s.sample.size;
    container.querySelector("#input-disk-rate").value = s.sample.ms_per_cyl || 1.0;
    await executeRun();
  });

  container.querySelector("#btn-disk-large").addEventListener("click", async () => {
    const s = await API.getSamples("disk");
    container.querySelector("#input-disk-queue").value = s.large.requests.join(", ");
    container.querySelector("#input-disk-head").value = s.large.head;
    container.querySelector("#input-disk-size").value = s.large.size;
    container.querySelector("#input-disk-rate").value = s.large.ms_per_cyl || 0.8;
    await executeRun();
  });

  container.querySelector("#btn-disk-random").addEventListener("click", async () => {
    const size = parseInt(container.querySelector("#input-disk-size").value) || 200;
    const len = 8 + Math.floor(Math.random() * 8);
    const randReqs = Array.from({ length: len }, () => Math.floor(Math.random() * size));
    const randHead = Math.floor(Math.random() * size);

    container.querySelector("#input-disk-queue").value = randReqs.join(", ");
    container.querySelector("#input-disk-head").value = randHead;
    await executeRun();
  });

  container.querySelector("#btn-disk-toggle-view").addEventListener("click", () => {
    isClassicView = !isClassicView;
    const classicEl = container.querySelector("#disk-classical-container");
    classicEl.style.display = isClassicView ? "flex" : "none";
    if (isClassicView && activeResult) {
      const canvas = container.querySelector("#disk-classical-canvas");
      renderClassicalDiskChart(canvas, activeResult.steps, currentParams.size);
    }
  });

  // Playback & Step
  container.querySelector("#btn-disk-step").addEventListener("click", () => {
    if (!activeResult || !activeResult.steps.length) return;
    playbackStep = (playbackStep + 1) % activeResult.steps.length;
    container.querySelectorAll("#disk-trace-tbody tr").forEach(r => r.style.background = "transparent");
    const activeRow = container.querySelector(`#disk-trace-row-${playbackStep}`);
    if (activeRow) {
      activeRow.style.background = "rgba(100, 150, 255, 0.25)";
      activeRow.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  });

  container.querySelector("#btn-disk-play").addEventListener("click", () => {
    if (playbackInterval) {
      clearInterval(playbackInterval);
      playbackInterval = null;
      showToast("Playback paused", "info");
    } else {
      if (!activeResult) return;
      playbackStep = 0;
      showToast("Playing step playback...", "info");
      playbackInterval = setInterval(() => {
        if (!activeResult || playbackStep >= activeResult.steps.length) {
          clearInterval(playbackInterval);
          playbackInterval = null;
          return;
        }
        container.querySelectorAll("#disk-trace-tbody tr").forEach(r => r.style.background = "transparent");
        const activeRow = container.querySelector(`#disk-trace-row-${playbackStep}`);
        if (activeRow) {
          activeRow.style.background = "rgba(100, 150, 255, 0.25)";
          activeRow.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        playbackStep++;
      }, 450);
    }
  });

  // Initial Run on Load
  await executeRun();
}
