/**
 * ui.js - Peak Glow Interface Widgets, Glass Controls & Toast Notifications
 */

export function showToast(message, type = "info", duration = 4200) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `glass-toast ${type}`;

  const icon = type === "error" ? "⚠" : type === "success" ? "✓" : "ℹ";
  toast.innerHTML = `<span style="font-weight: bold; font-size: 15px;">${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "all 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px) scale(0.9)";
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

export function createSegmentedControl({ container, options, selected, onSelect }) {
  const wrapper = document.createElement("div");
  wrapper.className = "segmented-control";

  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `segmented-option ${opt.value === selected ? 'active' : ''}`;
    btn.textContent = opt.label;

    btn.addEventListener("click", () => {
      wrapper.querySelectorAll(".segmented-option").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      if (onSelect) onSelect(opt.value);
    });

    wrapper.appendChild(btn);
  });

  if (container) container.appendChild(wrapper);
  return wrapper;
}

export function animateCountUp(element, targetVal, durationMs = 1200) {
  const startVal = parseFloat(element.textContent) || 0;
  const startTime = performance.now();
  const isFloat = targetVal % 1 !== 0;

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(1.0, elapsed / durationMs);
    const current = startVal + (targetVal - startVal) * (1 - Math.pow(1 - progress, 3));

    element.textContent = isFloat ? current.toFixed(2) : Math.round(current);

    if (progress < 1.0) {
      requestAnimationFrame(step);
    } else {
      element.textContent = isFloat ? targetVal.toFixed(2) : targetVal;
    }
  }

  requestAnimationFrame(step);
}

export function openDrawer(title, contentElement) {
  let drawer = document.getElementById("app-modal-drawer");
  if (!drawer) {
    drawer = document.createElement("div");
    drawer.id = "app-modal-drawer";
    drawer.style.position = "fixed";
    drawer.style.inset = "0";
    drawer.style.background = "rgba(4, 8, 16, 0.75)";
    drawer.style.backdropFilter = "blur(18px)";
    drawer.style.zIndex = "10000";
    drawer.style.display = "flex";
    drawer.style.justifyContent = "flex-end";
    drawer.style.transition = "opacity 0.3s ease";
    document.body.appendChild(drawer);
  }

  drawer.innerHTML = `
    <div style="width: min(650px, 92vw); height: 100%; background: var(--glass-elevated); border-left: 1px solid var(--glass-border); padding: 28px; display: flex; flex-direction: column; overflow: hidden; box-shadow: -10px 0 40px rgba(0,0,0,0.8);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--glass-border); padding-bottom: 14px;">
        <h2 style="font-size: 18px; font-weight: 600; color: #fff;">${title}</h2>
        <button id="drawer-close-btn" class="glass-btn glass-btn-sm" style="border-radius: 50%; width: 30px; height: 30px; padding: 0;">✕</button>
      </div>
      <div id="drawer-body" style="flex: 1; overflow-y: auto;"></div>
    </div>
  `;

  drawer.style.display = "flex";
  drawer.querySelector("#drawer-body").appendChild(contentElement);

  const closeBtn = drawer.querySelector("#drawer-close-btn");
  closeBtn.addEventListener("click", () => {
    drawer.style.display = "none";
  });

  drawer.addEventListener("click", (e) => {
    if (e.target === drawer) drawer.style.display = "none";
  });
}
