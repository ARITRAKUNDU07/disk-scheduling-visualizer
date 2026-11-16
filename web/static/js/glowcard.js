/**
 * glowcard.js - Peak Glow High-Fidelity Canvas Card Renderer
 *
 * Implements the full mathematical specification of the Peak Glow design system:
 * - 540:696 scaled unit coordinate frame
 * - Per-pixel offscreen synthesized multi-Gaussian potential field & bottom rims
 * - Halo light bleed, alpha-masked coordinate grid, and animated comet line
 * - Pulsing target dot, hover readout glass pill, and accessible dropdown listbox
 */

// PRNG: Mulberry32 for deterministic grain noise
function createMulberry32(seed) {
  let s = seed | 0;
  return function() {
    s = (s + 0x6D2B79F5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Error function approximation (Abramowitz & Stegun 7.1.26)
function erf(x) {
  const sign = x >= 0 ? 1 : -1;
  const a = Math.abs(x);
  const t = 1.0 / (1.0 + 0.3275911 * a);
  const y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-a * a);
  return sign * y;
}

// Normal Cumulative Distribution Function
function phi(x, mean, sigma) {
  return 0.5 * (1.0 + erf((x - mean) / (sigma * Math.SQRT2)));
}

// Signed Distance Function for Rounded Rectangle
function sdfRoundedRect(px, py, rx, ry, r) {
  const qx = Math.abs(px) - rx + r;
  const qy = Math.abs(py) - ry + r;
  return Math.min(Math.max(qx, qy), 0.0) + Math.hypot(Math.max(qx, 0.0), Math.max(qy, 0.0)) - r;
}

// Color parsing utilities
function hexToRgb(hex) {
  const cleaned = hex.replace("#", "");
  const num = parseInt(cleaned.length === 3 ? cleaned.split("").map(c => c + c).join("") : cleaned, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  };
}

// Compute CSS filter (hue-rotate, saturate) relative to base accent #4f8ef7
function computeAccentFilter(targetHex) {
  if (!targetHex || targetHex.toLowerCase() === "#4f8ef7") return "none";
  // Pre-calculated hue rotations from #4f8ef7:
  const map = {
    "#8a6df2": "hue-rotate(45deg) saturate(1.2)",
    "#2ec99a": "hue-rotate(120deg) saturate(1.1)",
    "#f0a23a": "hue-rotate(185deg) saturate(1.3)",
    "#f08a8a": "hue-rotate(240deg) saturate(1.2)",
  };
  return map[targetHex.toLowerCase()] || "none";
}

// Easing functions
const Easing = {
  easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  easeOutCubic: t => 1 - Math.pow(1 - t, 3),
  easeOutBack: t => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  }
};

/**
 * Factory function creating an active Glow Card instance inside a container.
 */
export function createGlowCard(options) {
  const {
    container,
    title = "Analysis",
    status = "Active",
    value = 0,
    unit = "",
    caption = "",
    accent = "#4f8ef7",
    width = 300,
    points = [], // array of numeric values or {x, y, isJump}
    optionsList = [],
    selectedOption = "",
    onOptionSelect = null,
    isStraight = false, // real straight segments (for Disk head movement)
    trend = null, // "up", "down", or null
  } = options;

  // Geometry
  const CARD_WIDTH = width;
  const CARD_HEIGHT = (width * 696) / 540;
  const u = CARD_WIDTH / 540;
  const rCard = (56 / 540) * CARD_WIDTH;
  const bleedX = 0.32 * CARD_WIDTH;
  const bleedY = 0.16 * CARD_WIDTH;

  const totalCanvasWidth = CARD_WIDTH + bleedX * 2;
  const totalCanvasHeight = CARD_HEIGHT + bleedY * 2;

  // Root wrapper element
  const cardEl = document.createElement("div");
  cardEl.className = "glow-card-container";
  cardEl.style.position = "relative";
  cardEl.style.width = `${CARD_WIDTH}px`;
  cardEl.style.height = `${CARD_HEIGHT}px`;
  cardEl.style.margin = "0 auto";
  cardEl.style.userSelect = "none";

  // Canvas element
  const canvas = document.createElement("canvas");
  canvas.className = "glow-card-canvas";
  canvas.style.position = "absolute";
  canvas.style.left = `${-bleedX}px`;
  canvas.style.top = `${-bleedY}px`;
  canvas.style.width = `${totalCanvasWidth}px`;
  canvas.style.height = `${totalCanvasHeight}px`;
  canvas.style.filter = computeAccentFilter(accent);
  canvas.style.pointerEvents = "auto";
  canvas.style.touchAction = "pan-y";

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(totalCanvasWidth * dpr);
  canvas.height = Math.round(totalCanvasHeight * dpr);

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  cardEl.appendChild(canvas);

  // Overlay DOM for accessible typography and interactive dropdowns
  const overlay = document.createElement("div");
  overlay.className = "glow-card-overlay";
  overlay.style.position = "absolute";
  overlay.style.inset = "0";
  overlay.style.pointerEvents = "none";
  overlay.style.borderRadius = `${rCard}px`;
  overlay.style.overflow = "hidden";
  cardEl.appendChild(overlay);

  // Status Top-Left
  const statusEl = document.createElement("div");
  statusEl.className = "glow-card-status";
  statusEl.style.position = "absolute";
  statusEl.style.top = `${28 * u}px`;
  statusEl.style.left = `${32 * u}px`;
  statusEl.style.fontSize = `${13 * u}px`;
  statusEl.style.color = "var(--text-dim)";
  statusEl.style.fontWeight = "400";
  statusEl.textContent = status;
  overlay.appendChild(statusEl);

  // Title Centered
  const titleEl = document.createElement("div");
  titleEl.className = "glow-card-title";
  titleEl.style.position = "absolute";
  titleEl.style.top = `${74 * u}px`;
  titleEl.style.width = "100%";
  titleEl.style.textAlign = "center";
  titleEl.style.fontSize = `${16 * u}px`;
  titleEl.style.color = "var(--text-faint)";
  titleEl.style.fontWeight = "400";
  titleEl.style.letterSpacing = "0.5px";
  titleEl.textContent = title;
  overlay.appendChild(titleEl);

  // Big Headline Number + Trend
  const headlineWrap = document.createElement("div");
  headlineWrap.style.position = "absolute";
  headlineWrap.style.top = `${102 * u}px`;
  headlineWrap.style.width = "100%";
  headlineWrap.style.textAlign = "center";
  headlineWrap.style.display = "flex";
  headlineWrap.style.alignItems = "baseline";
  headlineWrap.style.justifyContent = "center";
  headlineWrap.style.gap = `${6 * u}px`;

  const numberEl = document.createElement("span");
  numberEl.className = "glow-card-number";
  numberEl.style.fontSize = `${64 * u}px`;
  numberEl.style.fontWeight = "500";
  numberEl.style.color = "#ffffff";
  numberEl.style.fontVariantNumeric = "tabular-nums";
  numberEl.style.lineHeight = "1";
  numberEl.textContent = "0";

  const unitEl = document.createElement("span");
  unitEl.style.fontSize = `${18 * u}px`;
  unitEl.style.color = "var(--text-mid)";
  unitEl.textContent = unit;

  headlineWrap.appendChild(numberEl);
  headlineWrap.appendChild(unitEl);

  if (trend) {
    const trendEl = document.createElement("span");
    trendEl.style.fontSize = `${18 * u}px`;
    trendEl.style.marginLeft = `${4 * u}px`;
    if (trend === "up") {
      trendEl.textContent = "↑";
      trendEl.style.color = "var(--good)";
    } else {
      trendEl.textContent = "↓";
      trendEl.style.color = "var(--bad)";
    }
    headlineWrap.appendChild(trendEl);
  }

  overlay.appendChild(headlineWrap);

  // Caption Centered
  const captionEl = document.createElement("div");
  captionEl.className = "glow-card-caption";
  captionEl.style.position = "absolute";
  captionEl.style.top = `${186 * u}px`;
  captionEl.style.width = "100%";
  captionEl.style.textAlign = "center";
  captionEl.style.fontSize = `${11.5 * u}px`;
  captionEl.style.color = "var(--text-mid)";
  captionEl.textContent = caption;
  overlay.appendChild(captionEl);

  // Dropdown Pill (Top-Right)
  let dropdownBtn = null;
  let listboxEl = null;

  if (optionsList && optionsList.length > 0) {
    const dropdownWrap = document.createElement("div");
    dropdownWrap.style.position = "absolute";
    dropdownWrap.style.top = `${24 * u}px`;
    dropdownWrap.style.right = `${28 * u}px`;
    dropdownWrap.style.pointerEvents = "auto";
    dropdownWrap.style.zIndex = "10";

    dropdownBtn = document.createElement("button");
    dropdownBtn.setAttribute("aria-haspopup", "listbox");
    dropdownBtn.setAttribute("aria-expanded", "false");
    dropdownBtn.style.background = "rgba(255, 255, 255, 0.12)";
    dropdownBtn.style.border = "1px solid rgba(255, 255, 255, 0.15)";
    dropdownBtn.style.borderRadius = "20px";
    dropdownBtn.style.padding = `${4 * u}px ${12 * u}px`;
    dropdownBtn.style.color = "#ffffff";
    dropdownBtn.style.fontSize = `${12 * u}px`;
    dropdownBtn.style.display = "flex";
    dropdownBtn.style.alignItems = "center";
    dropdownBtn.style.gap = `${6 * u}px`;
    dropdownBtn.style.cursor = "pointer";
    dropdownBtn.style.backdropFilter = "blur(10px)";
    dropdownBtn.innerHTML = `<span>${selectedOption || optionsList[0]}</span> <span style="font-size: 8px;">▼</span>`;

    listboxEl = document.createElement("ul");
    listboxEl.setAttribute("role", "listbox");
    listboxEl.style.position = "absolute";
    listboxEl.style.top = "110%";
    listboxEl.style.right = "0";
    listboxEl.style.background = "rgba(18, 34, 66, 0.94)";
    listboxEl.style.border = "1px solid rgba(255, 255, 255, 0.16)";
    listboxEl.style.borderRadius = `${14 * u}px`;
    listboxEl.style.backdropFilter = "blur(18px) saturate(150%)";
    listboxEl.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6)";
    listboxEl.style.padding = "6px";
    listboxEl.style.listStyle = "none";
    listboxEl.style.display = "none";
    listboxEl.style.minWidth = `${120 * u}px`;

    optionsList.forEach(opt => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.style.padding = `${6 * u}px ${12 * u}px`;
      li.style.fontSize = `${12 * u}px`;
      li.style.borderRadius = `${8 * u}px`;
      li.style.color = opt === selectedOption ? "#ffffff" : "var(--text-dim)";
      li.style.background = opt === selectedOption ? "rgba(255,255,255,0.12)" : "transparent";
      li.style.cursor = "pointer";
      li.textContent = opt;

      li.addEventListener("click", e => {
        e.stopPropagation();
        listboxEl.style.display = "none";
        dropdownBtn.setAttribute("aria-expanded", "false");
        dropdownBtn.querySelector("span").textContent = opt;
        if (onOptionSelect) onOptionSelect(opt);
      });
      listboxEl.appendChild(li);
    });

    dropdownBtn.addEventListener("click", e => {
      e.stopPropagation();
      const isOpen = listboxEl.style.display === "block";
      listboxEl.style.display = isOpen ? "none" : "block";
      dropdownBtn.setAttribute("aria-expanded", !isOpen);
    });

    document.addEventListener("click", () => {
      if (listboxEl) {
        listboxEl.style.display = "none";
        dropdownBtn.setAttribute("aria-expanded", "false");
      }
    });

    dropdownWrap.appendChild(dropdownBtn);
    dropdownWrap.appendChild(listboxEl);
    overlay.appendChild(dropdownWrap);
  }

  // Hover Readout Glass Pill
  const readoutPill = document.createElement("div");
  readoutPill.className = "glow-card-readout";
  readoutPill.style.position = "absolute";
  readoutPill.style.background = "rgba(18, 36, 72, 0.65)";
  readoutPill.style.border = "1px solid rgba(160, 195, 255, 0.22)";
  readoutPill.style.borderRadius = "12px";
  readoutPill.style.padding = `${4 * u}px ${10 * u}px`;
  readoutPill.style.color = "#ffffff";
  readoutPill.style.fontSize = `${11 * u}px`;
  readoutPill.style.backdropFilter = "blur(10px)";
  readoutPill.style.pointerEvents = "none";
  readoutPill.style.display = "none";
  readoutPill.style.transform = "translate(-50%, -130%)";
  readoutPill.style.whiteSpace = "nowrap";
  readoutPill.style.zIndex = "20";
  overlay.appendChild(readoutPill);

  // ---------------------------------------------------------------------------
  // Canvas Rendering Infrastructure
  // ---------------------------------------------------------------------------

  let currentPoints = normalizePoints(points);
  let targetPoints = [...currentPoints];
  let morphProgress = 1.0;
  let morphStartPoints = [...currentPoints];

  let displayNum = 0;
  let targetNum = typeof value === "number" ? value : 0;
  let numProgress = 0.0;

  let animStartTime = performance.now();
  let isHovered = false;
  let hoverX = 0;
  let hoverY = 0;
  let hoveredPoint = null;

  // Offscreen Glow Field Canvas (Cached at ~540x696)
  const offscreenField = document.createElement("canvas");
  offscreenField.width = 540;
  offscreenField.height = 696;
  const offCtx = offscreenField.getContext("2d");
  paintGlowField(offCtx, 540, 696);

  // Offscreen Bright Breath Copy (with BREATH_GAIN 0.42)
  const offscreenBreath = document.createElement("canvas");
  offscreenBreath.width = 540;
  offscreenBreath.height = 696;
  const offBreathCtx = offscreenBreath.getContext("2d");
  paintGlowField(offBreathCtx, 540, 696, 0.42);

  function normalizePoints(rawPts) {
    if (!rawPts || rawPts.length === 0) {
      // Default sinusoidal hill
      return Array.from({ length: 40 }, (_, i) => ({
        x: i / 39,
        y: 0.5 + 0.35 * Math.sin((i / 39) * Math.PI),
        isJump: false,
        label: `Point ${i + 1}`,
        rawVal: (0.5 + 0.35 * Math.sin((i / 39) * Math.PI)).toFixed(2)
      }));
    }

    if (typeof rawPts[0] === "number") {
      const minVal = Math.min(...rawPts);
      const maxVal = Math.max(...rawPts);
      const span = maxVal - minVal || 1;
      return rawPts.map((v, i) => ({
        x: rawPts.length > 1 ? i / (rawPts.length - 1) : 0.5,
        y: 0.15 + 0.70 * ((v - minVal) / span),
        isJump: false,
        label: `Step ${i + 1}`,
        rawVal: v
      }));
    }

    return rawPts;
  }

  // Pre-render the Gaussian shades and SDF bottom rims
  function paintGlowField(targetCtx, w, h, breathGain = 0.0) {
    const imgData = targetCtx.createImageData(w, h);
    const data = imgData.data;

    const baseColor = hexToRgb("#1678ff");
    const shades = [
      { geom: [0.4748, 0.8152, 0.7509, 0.8801, 0.7026], color: hexToRgb("#000000"), opacity: 1.0 },
      { geom: [0.3741, 0.2723, 0.7371, 0.3009, 0.1168], color: hexToRgb("#020000"), opacity: 1.0 },
      { geom: [0.7846, 0.0251, 0.3833, 0.1301, -0.5566], color: hexToRgb("#2e85ff"), opacity: 0.4756 },
      { geom: [0.6206, -0.2018, 0.1282, 0.5909, 0.2754], color: hexToRgb("#3584ff"), opacity: 0.3146 },
      { geom: [0.6000, 1.2391, 0.8270, 0.2111, -1.6357], color: hexToRgb("#000d1e"), opacity: 1.0 },
      { geom: [0.0964, 0.5388, 1000.0, 0.1285, 0.5421], color: hexToRgb("#000005"), opacity: 0.2298 },
    ];

    const rims = [
      { geom: [0.1207, -0.0365, 0.0492], color: hexToRgb("#2667ff"), opacity: 1.0 + breathGain },
      { geom: [0.0667, -0.0166, 0.0176], color: hexToRgb("#467dff"), opacity: 1.0 + breathGain },
      { geom: [0.0370, -0.0134, 0.0154], color: hexToRgb("#c2ffff"), opacity: 0.8091 + breathGain },
    ];

    const rng = createMulberry32(1337);

    for (let py = 0; py < h; py++) {
      const v = py / w;
      for (let px = 0; px < w; px++) {
        const uCoord = px / w;
        let r = baseColor.r;
        let g = baseColor.g;
        let b = baseColor.b;

        // Blend shades
        for (const s of shades) {
          const [cx, cy, sx, sy, angle] = s.geom;
          const dx = uCoord - cx;
          const dy = v - cy;
          const cosA = Math.cos(-angle);
          const sinA = Math.sin(-angle);
          const rx = (dx * cosA - dy * sinA) / sx;
          const ry = (dx * sinA + dy * cosA) / sy;
          const distSq = rx * rx + ry * ry;
          const factor = s.opacity * Math.exp(-0.5 * distSq);

          r = r * (1 - factor) + s.color.r * factor;
          g = g * (1 - factor) + s.color.g * factor;
          b = b * (1 - factor) + s.color.b * factor;
        }

        // Blend bottom rims
        for (const rm of rims) {
          const [offset, spread, softness] = rm.geom;
          const rimDist = (h / w) - v - offset;
          const rimFactor = rm.opacity * (1.0 - phi(rimDist, spread, softness));
          if (rimFactor > 0) {
            const f = Math.min(1.0, rimFactor);
            r = r * (1 - f) + rm.color.r * f;
            g = g * (1 - f) + rm.color.g * f;
            b = b * (1 - f) + rm.color.b * f;
          }
        }

        // Grain noise (amplitude 1.7)
        const grain = (rng() - 0.5) * 3.4;
        const pIdx = (py * w + px) * 4;
        data[pIdx] = Math.min(255, Math.max(0, r + grain));
        data[pIdx + 1] = Math.min(255, Math.max(0, g + grain));
        data[pIdx + 2] = Math.min(255, Math.max(0, b + grain));
        data[pIdx + 3] = 255;
      }
    }
    targetCtx.putImageData(imgData, 0, 0);
  }

  // Draw Behind Halo Light
  function drawHalo(elapsedSec) {
    const cx = bleedX + 0.4996 * CARD_WIDTH;
    const cy = bleedY + 0.6438 * CARD_WIDTH;
    const rx = 0.2498 * CARD_WIDTH;
    const ry = 0.2433 * CARD_WIDTH;

    ctx.save();
    const haloGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rx * 1.8);
    haloGrad.addColorStop(0, "rgba(14, 80, 255, 0.45)");
    haloGrad.addColorStop(0.5, "rgba(22, 120, 255, 0.18)");
    haloGrad.addColorStop(1, "rgba(14, 80, 255, 0)");
    ctx.fillStyle = haloGrad;
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx * 1.8, ry * 1.8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // Draw Faint Alpha-Masked Grid
  function drawGrid(alphaFade) {
    if (alphaFade <= 0.01) return;
    const gridStepX = 40.64 * u;
    const gridStepY = 40.07 * u;

    ctx.save();
    ctx.strokeStyle = `rgba(90, 135, 225, ${0.18 * alphaFade})`;
    ctx.lineWidth = 1;

    const startX = 0;
    const endX = CARD_WIDTH;
    const startY = 220 * u;
    const endY = CARD_HEIGHT;

    ctx.beginPath();
    for (let x = startX; x <= endX; x += gridStepX) {
      ctx.moveTo(x, startY);
      ctx.lineTo(x, endY);
    }
    for (let y = startY; y <= endY; y += gridStepY) {
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  // Canvas Mouse Interaction for Readout
  canvas.addEventListener("mousemove", e => {
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left - bleedX;
    const clientY = e.clientY - rect.top - bleedY;

    if (clientX >= 0 && clientX <= CARD_WIDTH && clientY >= 200 * u && clientY <= CARD_HEIGHT) {
      isHovered = true;
      hoverX = clientX;
      hoverY = clientY;
    } else {
      isHovered = false;
      readoutPill.style.display = "none";
    }
  });

  canvas.addEventListener("mouseleave", () => {
    isHovered = false;
    readoutPill.style.display = "none";
  });

  // Main Render Loop
  let rafId = null;

  function render(now) {
    const elapsedSec = (now - animStartTime) / 1000.0;
    ctx.clearRect(0, 0, totalCanvasWidth, totalCanvasHeight);

    // 1. Draw Halo
    drawHalo(elapsedSec);

    // 2. Clip inside rounded card path
    ctx.save();
    ctx.translate(bleedX, bleedY);
    ctx.beginPath();
    ctx.roundRect(0, 0, CARD_WIDTH, CARD_HEIGHT, rCard);
    ctx.clip();

    // 3. Blit Glow Field
    ctx.drawImage(offscreenField, 0, 0, CARD_WIDTH, CARD_HEIGHT);

    // 4. Harmonic Breath Layer (4.6s cycle)
    const breath = Math.pow(Math.sin((Math.PI * elapsedSec) / 4.6), 2);
    ctx.save();
    ctx.globalAlpha = breath * 0.7;
    ctx.drawImage(offscreenBreath, 0, 0, CARD_WIDTH, CARD_HEIGHT);
    ctx.restore();

    // 5. Grid Fade In
    const gridAlpha = Math.min(1.0, elapsedSec / 0.9);
    drawGrid(gridAlpha);

    // 6. Draw Line & Comet
    const lineDrawDuration = 2.1;
    const lineDelay = 0.25;
    const lineT = Math.min(1.0, Math.max(0.0, (elapsedSec - lineDelay) / lineDrawDuration));
    const lineEased = Easing.easeInOutCubic(lineT);

    // Handle morphing between datasets
    if (morphProgress < 1.0) {
      morphProgress = Math.min(1.0, morphProgress + 0.035);
      const mEased = Easing.easeInOutCubic(morphProgress);
      currentPoints = targetPoints.map((tp, idx) => {
        const sp = morphStartPoints[idx] || tp;
        return {
          ...tp,
          x: sp.x + (tp.x - sp.x) * mEased,
          y: sp.y + (tp.y - sp.y) * mEased,
        };
      });
    }

    // Number Tween
    if (numProgress < 1.0 && elapsedSec > 0.8) {
      numProgress = Math.min(1.0, numProgress + 0.025);
      const nEased = Easing.easeOutCubic(numProgress);
      displayNum = targetNum * nEased;
      if (typeof targetNum === "number") {
        numberEl.textContent = targetNum % 1 === 0 ? Math.round(displayNum) : displayNum.toFixed(2);
      }
    }

    // Convert normalized coordinates to canvas space
    const plotYBottom = CARD_HEIGHT - 35 * u;
    const plotHeight = 360 * u;

    const canvasPts = currentPoints.map(p => ({
      cx: 40 * u + p.x * (CARD_WIDTH - 80 * u),
      cy: plotYBottom - p.y * plotHeight,
      isJump: p.isJump,
      label: p.label,
      rawVal: p.rawVal
    }));

    if (canvasPts.length > 0) {
      const activeLength = Math.max(1, Math.floor(canvasPts.length * lineEased));
      const activePts = canvasPts.slice(0, activeLength);

      // Draw Main Line
      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      for (let i = 0; i < activePts.length - 1; i++) {
        const p1 = activePts[i];
        const p2 = activePts[i + 1];

        ctx.beginPath();
        ctx.moveTo(p1.cx, p1.cy);
        ctx.lineTo(p2.cx, p2.cy);

        if (p2.isJump) {
          ctx.strokeStyle = "var(--jump)";
          ctx.lineWidth = 4 * u;
          ctx.setLineDash([6 * u, 6 * u]);
        } else {
          ctx.strokeStyle = "var(--line)";
          ctx.lineWidth = 6 * u;
          ctx.setLineDash([]);
        }
        ctx.stroke();
      }
      ctx.restore();

      // Leading Tip / Target Dot
      let targetPt = activePts[activePts.length - 1];
      if (isHovered) {
        // Find closest point to mouse
        let closest = activePts[0];
        let minD = Math.hypot(closest.cx - hoverX, closest.cy - hoverY);
        for (const pt of activePts) {
          const d = Math.hypot(pt.cx - hoverX, pt.cy - hoverY);
          if (d < minD) {
            minD = d;
            closest = pt;
          }
        }
        targetPt = closest;
        readoutPill.style.display = "block";
        readoutPill.style.left = `${targetPt.cx}px`;
        readoutPill.style.top = `${targetPt.cy}px`;
        readoutPill.innerHTML = `<strong>${targetPt.label || 'Val'}</strong>: ${targetPt.rawVal}`;
      }

      if (targetPt) {
        const dotR = 11 * u;
        // Outer Radial Glow
        const haloGrad = ctx.createRadialGradient(targetPt.cx, targetPt.cy, 0, targetPt.cx, targetPt.cy, 28 * u);
        haloGrad.addColorStop(0, "rgba(40, 125, 255, 0.7)");
        haloGrad.addColorStop(1, "rgba(40, 125, 255, 0)");
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(targetPt.cx, targetPt.cy, 28 * u, 0, Math.PI * 2);
        ctx.fill();

        // Inner Dot Gradient
        const dotGrad = ctx.createRadialGradient(targetPt.cx, targetPt.cy, 0, targetPt.cx, targetPt.cy, dotR);
        dotGrad.addColorStop(0, "#d0e4fd");
        dotGrad.addColorStop(0.45, "#75aafa");
        dotGrad.addColorStop(1, "#2680ff");
        ctx.fillStyle = dotGrad;
        ctx.beginPath();
        ctx.arc(targetPt.cx, targetPt.cy, dotR, 0, Math.PI * 2);
        ctx.fill();

        // Pulse wave when landing
        if (lineEased >= 1.0) {
          const pulseT = ((elapsedSec - 2.35) % 3.0);
          if (pulseT >= 0 && pulseT < 0.8) {
            const pFrac = pulseT / 0.8;
            ctx.save();
            ctx.strokeStyle = `rgba(120, 175, 255, ${1.0 - pFrac})`;
            ctx.lineWidth = 2 * u;
            ctx.beginPath();
            ctx.arc(targetPt.cx, targetPt.cy, dotR + pFrac * 22 * u, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();
          }
        }
      }
    }

    ctx.restore(); // unclip rounded card
    rafId = requestAnimationFrame(render);
  }

  // Start rendering
  rafId = requestAnimationFrame(render);
  if (container) container.appendChild(cardEl);

  // Return component control handle
  return {
    element: cardEl,
    update: newOpts => {
      if (newOpts.value !== undefined) {
        targetNum = typeof newOpts.value === "number" ? newOpts.value : 0;
        numProgress = 0.0;
        if (typeof targetNum !== "number") numberEl.textContent = targetNum;
      }
      if (newOpts.caption !== undefined) captionEl.textContent = newOpts.caption;
      if (newOpts.status !== undefined) statusEl.textContent = newOpts.status;
      if (newOpts.accent) canvas.style.filter = computeAccentFilter(newOpts.accent);
      if (newOpts.points) {
        morphStartPoints = [...currentPoints];
        targetPoints = normalizePoints(newOpts.points);
        morphProgress = 0.0;
      }
    },
    destroy: () => {
      if (rafId) cancelAnimationFrame(rafId);
      cardEl.remove();
    }
  };
}
