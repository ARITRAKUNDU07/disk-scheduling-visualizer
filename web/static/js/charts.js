/**
 * charts.js - Native Canvas 2D Visualizers (Gantt, Classical Disk, Frame Matrix)
 * 100% handcrafted offline graphics with zero external libraries.
 */

// Colors for CPU processes
const PROCESS_COLORS = [
  "#4f8ef7", "#8a6df2", "#2ec99a", "#f0a23a", "#f08a8a",
  "#38bdf8", "#a855f7", "#34d399", "#fb923c", "#f43f5e"
];

export function renderCPUGantt(canvas, ganttSegments) {
  if (!canvas || !ganttSegments || ganttSegments.length === 0) return;
  const ctx = canvas.getContext("2d");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const rect = canvas.getBoundingClientRect();
  const width = rect.width || 700;
  const height = rect.height || 160;

  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, width, height);

  const totalTime = Math.max(...ganttSegments.map(s => s.end), 1);
  const padLeft = 40;
  const padRight = 40;
  const barY = 40;
  const barHeight = 44;
  const usableWidth = width - padLeft - padRight;

  // Background track
  ctx.fillStyle = "rgba(14, 24, 46, 0.6)";
  ctx.beginPath();
  ctx.roundRect(padLeft, barY, usableWidth, barHeight, 8);
  ctx.fill();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.stroke();

  // Draw Segments
  const pidColorMap = {};
  let colorIdx = 0;

  ganttSegments.forEach(seg => {
    if (!pidColorMap[seg.pid]) {
      pidColorMap[seg.pid] = PROCESS_COLORS[colorIdx % PROCESS_COLORS.length];
      colorIdx++;
    }

    const segX = padLeft + (seg.start / totalTime) * usableWidth;
    const segW = ((seg.end - seg.start) / totalTime) * usableWidth;
    const color = pidColorMap[seg.pid];

    // Segment block with soft glow
    ctx.save();
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.roundRect(segX + 1, barY + 2, Math.max(segW - 2, 2), barHeight - 4, 6);
    ctx.fill();
    ctx.restore();

    // Segment PID label
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px var(--font-family, sans-serif)";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if (segW > 20) {
      ctx.fillText(seg.pid, segX + segW / 2, barY + barHeight / 2);
    }

    // Time ticks at bottom
    ctx.fillStyle = "var(--text-mid, #acc1e7)";
    ctx.font = "11px var(--font-mono, monospace)";
    ctx.textAlign = "center";
    ctx.fillText(`${seg.end:g}`, segX + segW, barY + barHeight + 20);
  });

  // Start tick 0
  ctx.fillStyle = "var(--text-mid, #acc1e7)";
  ctx.font = "11px var(--font-mono, monospace)";
  ctx.textAlign = "center";
  ctx.fillText("0", padLeft, barY + barHeight + 20);
}

export function renderClassicalDiskChart(canvas, steps, diskSize) {
  if (!canvas || !steps || steps.length === 0) return;
  const ctx = canvas.getContext("2d");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const rect = canvas.getBoundingClientRect();
  const width = rect.width || 700;
  const height = rect.height || 340;

  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, width, height);

  const padLeft = 40;
  const padRight = 40;
  const padTop = 30;
  const padBottom = 30;

  const usableWidth = width - padLeft - padRight;
  const usableHeight = height - padTop - padBottom;
  const numSteps = steps.length;

  // Grid
  ctx.strokeStyle = "rgba(90, 135, 225, 0.12)";
  ctx.lineWidth = 1;

  for (let s = 0; s <= numSteps; s++) {
    const y = padTop + (s / numSteps) * usableHeight;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(padLeft + usableWidth, y);
    ctx.stroke();
  }

  // Draw Head Motion Path
  ctx.lineWidth = 2.5;
  ctx.lineCap = "round";

  let currCyl = steps[0].from_cyl;
  let currX = padLeft + (currCyl / (diskSize - 1)) * usableWidth;
  let currY = padTop;

  // Initial head dot
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(currX, currY, 5, 0, Math.PI * 2);
  ctx.fill();

  steps.forEach((st, idx) => {
    const nextX = padLeft + (st.to_cyl / (diskSize - 1)) * usableWidth;
    const nextY = padTop + ((idx + 1) / numSteps) * usableHeight;

    ctx.beginPath();
    ctx.moveTo(currX, currY);
    ctx.lineTo(nextX, nextY);

    if (st.is_jump) {
      ctx.strokeStyle = "#f59e0b"; // amber for return jump
      ctx.setLineDash([5, 5]);
    } else {
      ctx.strokeStyle = "#6496e2";
      ctx.setLineDash([]);
    }
    ctx.stroke();

    // Dot at destination
    ctx.fillStyle = st.is_jump ? "#f59e0b" : "#78afff";
    ctx.beginPath();
    ctx.arc(nextX, nextY, 4, 0, Math.PI * 2);
    ctx.fill();

    currX = nextX;
    currY = nextY;
  });

  // Cylinder axis labels
  ctx.fillStyle = "var(--text-mid, #acc1e7)";
  ctx.font = "11px var(--font-mono, monospace)";
  ctx.textAlign = "left";
  ctx.fillText("0", padLeft, padTop - 10);
  ctx.textAlign = "right";
  ctx.fillText(`${diskSize - 1}`, padLeft + usableWidth, padTop - 10);
  ctx.textAlign = "center";
  ctx.fillText("Cylinder Position →", padLeft + usableWidth / 2, padTop - 10);
}
