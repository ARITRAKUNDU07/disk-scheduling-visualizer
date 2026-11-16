/**
 * views/deadlock.js - Banker's Deadlock Avoidance Studio
 * Matrix Grids Editor | Animated Safe Sequence Flow | Dynamic Request Sandbox
 */

import { API } from "../api.js";
import { createGlowCard } from "../glowcard.js";
import { showToast } from "../ui.js";

export async function renderDeadlockView(container) {
  let available = [3, 3, 2];
  let allocation = {
    P0: [0, 1, 0],
    P1: [2, 0, 0],
    P2: [3, 0, 2],
    P3: [2, 1, 1],
    P4: [0, 0, 2]
  };
  let maxMatrix = {
    P0: [7, 5, 3],
    P1: [3, 2, 2],
    P2: [9, 0, 2],
    P3: [2, 2, 2],
    P4: [4, 3, 3]
  };

  let activeGlowCard = null;

  container.innerHTML = `
    <div class="deadlock-view-container" style="display: flex; flex-direction: column; gap: 24px;">
      <!-- Upper Section: Matrices & Glow Card -->
      <div style="display: grid; grid-template-columns: minmax(360px, 1.4fr) minmax(320px, 1fr); gap: 20px; align-items: start;">
        
        <!-- Column 1: Editable Matrix Grids -->
        <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="font-size: 16px; font-weight: 600; color: #fff;">System Resource State</h2>
            <div style="display: flex; gap: 6px;">
              <button id="btn-deadlock-sample" class="glass-btn glass-btn-sm">Sample (5x3)</button>
              <button id="btn-deadlock-large" class="glass-btn glass-btn-sm">Large (6x4)</button>
            </div>
          </div>

          <!-- Available Vector -->
          <div class="form-group" style="margin-bottom: 8px;">
            <label class="form-label">Available Vector (A, B, C...)</label>
            <input id="input-deadlock-avail" class="glass-input" type="text" value="${available.join(', ')}">
          </div>

          <!-- Process Allocation & Max Claims Grids -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
              <span class="form-label">Allocation Matrix</span>
              <div class="glass-table-wrapper" style="max-height: 200px; overflow-y: auto;">
                <table class="glass-table" id="table-deadlock-alloc">
                  <tbody id="tbody-deadlock-alloc"></tbody>
                </table>
              </div>
            </div>
            <div>
              <span class="form-label">Max Claim Matrix</span>
              <div class="glass-table-wrapper" style="max-height: 200px; overflow-y: auto;">
                <table class="glass-table" id="table-deadlock-max">
                  <tbody id="tbody-deadlock-max"></tbody>
                </table>
              </div>
            </div>
          </div>

          <div style="display: flex; gap: 8px; margin-top: 6px;">
            <button id="btn-deadlock-eval" class="glass-btn glass-btn-primary" style="flex: 1;">▶ Evaluate Safety</button>
          </div>
        </div>

        <!-- Column 2: Center Glow Card -->
        <div style="display: flex; justify-content: center;">
          <div id="deadlock-glow-card-target" style="width: 100%; display: flex; justify-content: center;"></div>
        </div>

      </div>

      <!-- Safe Sequence Visualization & Steps -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Safe Execution Sequence</h3>
          <span id="deadlock-status-badge" class="brand-badge">AWAITING EVALUATION</span>
        </div>
        
        <div id="deadlock-sequence-chips" style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 12px; background: rgba(14, 24, 46, 0.4); border-radius: 12px; border: 1px solid var(--glass-border);">
          <span style="color: var(--text-dim); font-size: 12px;">Execute safety algorithm to view sequence flow.</span>
        </div>

        <!-- Need Matrix Breakdown -->
        <div style="margin-top: 6px;">
          <h4 style="font-size: 13px; font-weight: 600; color: var(--text-mid); margin-bottom: 8px;">Calculated Need Matrix (Need = Max - Allocation)</h4>
          <div class="glass-table-wrapper">
            <table class="glass-table">
              <thead>
                <tr id="deadlock-need-thead"></tr>
              </thead>
              <tbody id="deadlock-need-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Resource Request Sandbox -->
      <div class="glass-panel" style="display: flex; flex-direction: column; gap: 14px;">
        <h3 style="font-size: 15px; font-weight: 600; color: #fff;">Ad-Hoc Resource Request Sandbox</h3>
        <p style="font-size: 12px; color: var(--text-mid);">
          Test hypothetical dynamic allocation with Banker's rollback algorithm without mutating original system state.
        </p>

        <div style="display: grid; grid-template-columns: minmax(140px, 1fr) minmax(240px, 2fr) auto; gap: 12px; align-items: flex-end;">
          <div class="form-group" style="margin: 0;">
            <label class="form-label">Requesting PID</label>
            <select id="select-deadlock-req-pid" class="glass-select"></select>
          </div>
          <div class="form-group" style="margin: 0;">
            <label class="form-label">Requested Vector</label>
            <input id="input-deadlock-req-vector" class="glass-input" type="text" placeholder="e.g. 1, 0, 2">
          </div>
          <button id="btn-deadlock-submit-req" class="glass-btn glass-btn-primary" style="height: 38px;">Test Allocation</button>
        </div>

        <div id="deadlock-request-result" class="glass-panel-elevated" style="display: none; font-size: 13px; line-height: 1.5;"></div>
      </div>
    </div>
  `;

  function renderMatrixInputs() {
    const allocTbody = container.querySelector("#tbody-deadlock-alloc");
    const maxTbody = container.querySelector("#tbody-deadlock-max");
    const reqPidSelect = container.querySelector("#select-deadlock-req-pid");

    allocTbody.innerHTML = "";
    maxTbody.innerHTML = "";
    reqPidSelect.innerHTML = "";

    for (const pid of Object.keys(allocation)) {
      // Allocation row
      const aTr = document.createElement("tr");
      aTr.innerHTML = `
        <td style="font-weight: bold; width: 40px;">${pid}</td>
        <td><input type="text" class="glass-input" style="padding: 4px 6px; font-size: 12px;" value="${allocation[pid].join(', ')}" data-alloc-pid="${pid}"></td>
      `;
      allocTbody.appendChild(aTr);

      // Max row
      const mTr = document.createElement("tr");
      mTr.innerHTML = `
        <td style="font-weight: bold; width: 40px;">${pid}</td>
        <td><input type="text" class="glass-input" style="padding: 4px 6px; font-size: 12px;" value="${maxMatrix[pid].join(', ')}" data-max-pid="${pid}"></td>
      `;
      maxTbody.appendChild(mTr);

      // Request Select
      const opt = document.createElement("option");
      opt.value = pid;
      opt.textContent = pid;
      reqPidSelect.appendChild(opt);
    }

    allocTbody.querySelectorAll("input").forEach(inp => {
      inp.addEventListener("change", e => {
        const pid = e.target.dataset.allocPid;
        allocation[pid] = e.target.value.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));
      });
    });

    maxTbody.querySelectorAll("input").forEach(inp => {
      inp.addEventListener("change", e => {
        const pid = e.target.dataset.maxPid;
        maxMatrix[pid] = e.target.value.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));
      });
    });
  }

  function setupDeadlockGlowCard(res) {
    const target = container.querySelector("#deadlock-glow-card-target");
    target.innerHTML = "";

    const isSafe = res ? res.is_safe : true;
    const availHistory = res ? res.available_history.map(v => v.reduce((a, b) => a + b, 0)) : available;

    activeGlowCard = createGlowCard({
      container: target,
      title: "BANKER'S SAFETY STATUS",
      status: `Evaluated · ${new Date().toLocaleTimeString()}`,
      value: isSafe ? "SAFE" : "UNSAFE",
      unit: "state",
      caption: res ? (isSafe ? `Safe Sequence: ${res.safe_sequence.join(' → ')}` : "System in Deadlock Hazard") : "Awaiting execution",
      accent: isSafe ? "var(--accent-deadlock)" : "var(--accent-unsafe)",
      width: 340,
      points: availHistory,
    });
  }

  function renderNeedMatrix(need) {
    const thead = container.querySelector("#deadlock-need-thead");
    const tbody = container.querySelector("#deadlock-need-tbody");
    const numRes = available.length;

    thead.innerHTML = `<th>PID</th>` + Array.from({ length: numRes }, (_, i) => `<th>R${i}</th>`).join("");
    tbody.innerHTML = "";

    for (const [pid, row] of Object.entries(need)) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td style="font-weight: bold;">${pid}</td>` + row.map(v => `<td>${v}</td>`).join("");
      tbody.appendChild(tr);
    }
  }

  function renderSafeSequence(res) {
    const chipsContainer = container.querySelector("#deadlock-sequence-chips");
    const badge = container.querySelector("#deadlock-status-badge");
    chipsContainer.innerHTML = "";

    if (res.is_safe) {
      badge.textContent = "VERIFIED SAFE STATE";
      badge.style.background = "rgba(147, 207, 162, 0.2)";
      badge.style.color = "var(--good)";

      res.safe_sequence.forEach((pid, idx) => {
        const chip = document.createElement("div");
        chip.style.background = "rgba(240, 162, 58, 0.2)";
        chip.style.border = "1px solid rgba(240, 162, 58, 0.4)";
        chip.style.borderRadius = "20px";
        chip.style.padding = "6px 14px";
        chip.style.color = "#fff";
        chip.style.fontWeight = "bold";
        chip.textContent = `${idx + 1}. ${pid}`;
        chipsContainer.appendChild(chip);

        if (idx < res.safe_sequence.length - 1) {
          const arrow = document.createElement("span");
          arrow.style.color = "var(--text-dim)";
          arrow.style.fontSize = "14px";
          arrow.textContent = "→";
          chipsContainer.appendChild(arrow);
        }
      });
    } else {
      badge.textContent = "CRITICAL UNSAFE STATE";
      badge.style.background = "rgba(240, 138, 138, 0.2)";
      badge.style.color = "var(--bad)";
      chipsContainer.innerHTML = `<span style="color: var(--bad); font-weight: bold;">${res.reason}</span>`;
    }
  }

  async function executeSafety() {
    const availStr = container.querySelector("#input-deadlock-avail").value;
    available = availStr.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));

    try {
      const res = await API.evaluateSafety({
        available,
        allocation,
        max: maxMatrix
      });

      if (!activeGlowCard) {
        setupDeadlockGlowCard(res);
      } else {
        activeGlowCard.update({
          value: res.is_safe ? "SAFE" : "UNSAFE",
          caption: res.is_safe ? `Sequence: ${res.safe_sequence.join(' → ')}` : "Deadlock Hazard",
          accent: res.is_safe ? "var(--accent-deadlock)" : "var(--accent-unsafe)",
          points: res.available_history.map(v => v.reduce((a, b) => a + b, 0))
        });
      }

      renderNeedMatrix(res.need_matrix);
      renderSafeSequence(res);

      if (res.is_safe) {
        showToast("System verified SAFE: Safe sequence established.", "success");
      } else {
        showToast("System verified UNSAFE: Deadlock could occur.", "error");
      }
    } catch (e) {
      // Error handled
    }
  }

  async function executeRequestTest() {
    const pid = container.querySelector("#select-deadlock-req-pid").value;
    const reqStr = container.querySelector("#input-deadlock-req-vector").value;
    const reqVector = reqStr.split(",").map(x => parseInt(x.trim())).filter(x => !isNaN(x));

    try {
      const res = await API.evaluateRequest({
        available,
        allocation,
        max: maxMatrix,
        pid,
        request: reqVector
      });

      const resBox = container.querySelector("#deadlock-request-result");
      resBox.style.display = "block";
      if (res.granted) {
        resBox.style.borderColor = "rgba(147, 207, 162, 0.4)";
        resBox.style.color = "var(--good)";
        resBox.innerHTML = `<strong>✓ REQUEST GRANTED:</strong> ${res.reason}`;
        showToast("Resource request is SAFE and GRANTED.", "success");
      } else {
        resBox.style.borderColor = "rgba(240, 138, 138, 0.4)";
        resBox.style.color = "var(--bad)";
        resBox.innerHTML = `<strong>✕ REQUEST DENIED:</strong> ${res.reason}`;
        showToast("Resource request DENIED.", "error");
      }
    } catch (e) {
      // Error handled
    }
  }

  // Hook Handlers
  container.querySelector("#btn-deadlock-eval").addEventListener("click", executeSafety);
  container.querySelector("#btn-deadlock-submit-req").addEventListener("click", executeRequestTest);

  container.querySelector("#btn-deadlock-sample").addEventListener("click", async () => {
    const s = await API.getSamples("banker");
    available = s.sample.available;
    allocation = s.sample.allocation;
    maxMatrix = s.sample.max;
    container.querySelector("#input-deadlock-avail").value = available.join(", ");
    renderMatrixInputs();
    await executeSafety();
  });

  container.querySelector("#btn-deadlock-large").addEventListener("click", async () => {
    const s = await API.getSamples("banker");
    available = s.large.available;
    allocation = s.large.allocation;
    maxMatrix = s.large.max;
    container.querySelector("#input-deadlock-avail").value = available.join(", ");
    renderMatrixInputs();
    await executeSafety();
  });

  renderMatrixInputs();
  await executeSafety();
}
