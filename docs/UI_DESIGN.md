# Peak Glow UI Design System Specification

**Design Theme:** Peak Glow (Cybernetic Glass & Luminous Vector Canvas)  
**Implementation:** Vanilla HTML5, Modern CSS Variables, Canvas 2D API (ES Modules)  
**Dependencies:** Zero external libraries, zero CDN fonts, zero node/npm packages. 100% Offline Capable.

---

## 1. Design Tokens & Color Palette

All styling originates from hardware-accelerated CSS custom properties declared at `:root`:

```css
:root {
  /* Surface Backdrops */
  --bg: #08101a;
  --bg-deep: #050b12;
  --bg-frame: rgba(10, 18, 30, 0.72);

  /* Glass Containers */
  --glass: rgba(20, 34, 64, 0.55);
  --glass-elevated: rgba(26, 44, 82, 0.70);
  --glass-border: rgba(255, 255, 255, 0.12);
  --glass-border-focus: rgba(140, 190, 255, 0.45);

  /* Typography Colors */
  --text-main: #f0f4fc;
  --text-dim: #99a3b6;
  --text-mid: #acc1e7;
  --text-faint: #9298a5;

  /* Luminous Vectors & Accents (Base: Ocean Blue) */
  --line: #6496e2;
  --glow: #1678ff;
  --dot-glow: #287dff;
  --pulse: #78afff;
  
  /* Semantic Status Tokens */
  --good: #93cfa2;       /* Positive performance, safe status */
  --bad: #f08a8a;        /* High waiting/faults, deadlock warning */
  --jump: #f59e0b;       /* Return jumps in C-SCAN / C-LOOK */
  --warning: #fbbf24;

  /* Subsystem Accent Themes (Hue Shift Matrix) */
  --accent-disk: #4f8ef7;      /* Base Cyan-Blue */
  --accent-cpu: #8a6df2;       /* Electric Violet */
  --accent-pages: #2ec99a;     /* Emerald Teal */
  --accent-deadlock: #f0a23a;  /* Luminous Amber (Safe) */
  --accent-unsafe: #f08a8a;    /* Warning Rose (Unsafe) */
}
```

---

## 2. Canvas Glow Card Architecture (`web/static/js/glowcard.js`)

The Glow Card is an ultra-high fidelity, hardware-composited canvas component ported directly from high-end generative design systems.

### 2.1 Geometry & Coordinate Normalization
- **Aspect Ratio:** Fixed at `540 : 696` (width:height).
- **Corner Radius:** `56 / 540` of width (`r = width * (56 / 540)`).
- **Scale Unit (`u`):** Every internal measurement (fonts, stroke widths, paddings, blur radii) scales proportionally with:
  $$\text{unit} = \frac{\text{width}}{540}$$
- **High-DPI Rendering:** Canvas buffer width is multiplied by `devicePixelRatio` (capped at `2.0` to preserve memory efficiency on integrated GPUs). Context is scaled by `dpr`, ensuring crisp vector boundaries on Retina and 4K displays.

### 2.2 Layered Compositing Stack
Each frame is painted in the following deterministic sequence:

1. **Halo Bleed (Backdrop Light Spill):**
   - Renders outside the card boundaries onto the background tile to create ambient depth.
   - Horizontal bleed: $BX = 0.32 \times 540u$. Vertical bleed: $BY = 0.16 \times 540u$.
   - Gaussian center: $c_x = 0.4996, c_y = 0.6438$; Radius: $s_x = 0.2498, s_y = 0.2433$; Opacity: $0.845$; Color: `#0e50ff`.

2. **Rounded Card Clipping:**
   - Inner canvas context is clipped to the continuous rounded rectangle path with radius `56u`.

3. **Glow Field (Multi-Gaussian Potential Map):**
   - Synthesized into an offscreen canvas at startup or dimension change, then blitted directly.
   - Starts with a solid foundation fill of `#1678ff`.
   - 6 Gaussian Ellipse Shades blended in rotated frames:
     1. $[0.4748, 0.8152, 0.7509, 0.8801, 0.7026]$ Color: `#000000`, Opacity: $1.0$
     2. $[0.3741, 0.2723, 0.7371, 0.3009, 0.1168]$ Color: `#020000`, Opacity: $1.0$
     3. $[0.7846, 0.0251, 0.3833, 0.1301, -0.5566]$ Color: `#2e85ff`, Opacity: $0.4756$
     4. $[0.6206, -0.2018, 0.1282, 0.5909, 0.2754]$ Color: `#3584ff`, Opacity: $0.3146$
     5. $[0.6000, 1.2391, 0.8270, 0.2111, -1.6357]$ Color: `#000d1e`, Opacity: $1.0$
     6. $[0.0964, 0.5388, 1000.0, 0.1285, 0.5421]$ Color: `#000005`, Opacity: $0.2298$
   - 3 Bottom Rim Glows computed via Signed Distance Function (SDF) and normal CDF:
     1. $[0.1207, -0.0365, 0.0492]$ Color: `#2667ff`, Opacity: $1.0$
     2. $[0.0667, -0.0166, 0.0176]$ Color: `#467dff`, Opacity: $1.0$
     3. $[0.0370, -0.0134, 0.0154]$ Color: `#c2ffff`, Opacity: $0.8091$

4. **Breathing Modulation Layer:**
   - Harmonic sine-squared breathing factor:
     $$\beta(t) = \sin^2\left(\frac{2\pi \cdot t}{4.6}\right)$$
   - Modulates the brightness of the lower rim glow with `BREATH_GAIN = 0.42`.

5. **Grid Layer:**
   - Grid spacing: $40.64u \times 40.07u$.
   - Stroke `#5a87e1` with max alpha $0.23$, alpha-masked so lines smoothly vanish towards the card header and lateral margins.

6. **Luminous Path & Comet Head:**
   - Path stroke `#6496e2`, stroke width $7.1u$, round line joins and caps.
   - For Disk head movements, path segments represent real physical cylinder-to-cylinder transitions.
   - Jump segments in C-SCAN/C-LOOK are drawn as dashed lines in `--jump` (`#f59e0b`).
   - While drawing (over $2.1\text{ s}$), a bright white-blue comet head trails behind the leading tip.

7. **Target Dot & Ripple Wave:**
   - Multi-stop radial gradient ($#2680ff \to #75aafa \to #d0e4fd$), radius $13u$.
   - Outer glow halo of $30u$ radius.
   - Target impact initiates a soft expanding pulse ring (`#78afff`) that dissipates across $0.8\text{ s}$.

---

## 3. Screen Layouts & Component Hierarchy

### 3.1 Global Application Shell
- **Backdrop:** Generated $160\times160\text{px}$ noise grain canvas tile synthesized via deterministic Mulberry32 PRNG (amplitude 1.7) and applied via data URL background pattern.
- **Outer Glass Frame:**
  - Inset: `clamp(10px, 2.6vmin, 26px)`
  - Border radius: `clamp(18px, 4.5vmin, 34px)`
  - Border: `1px solid rgba(140, 170, 230, 0.10)`
  - Background: `var(--bg-frame)` with backdrop filter blur `24px`.

### 3.2 Navigation & Views
1. **Dashboard (Executive Overview):**
   - 4 Glow Cards arranged in an adaptive responsive grid: Disk Scheduling, CPU Scheduling, Page Replacement, and Deadlock Avoidance.
   - Each card displays real-time optimal algorithm headlines from `/api/summary`.
   - Bottom floating Glass Action Toolbar: Full Analysis, Markdown Report, Audit Log Summary, System Diagnostics, Run Test Suite.
2. **Disk Scheduling Studio (Flagship Screen):**
   - Control Console: Cylinder queue input, head starting position, disk boundary slider, direction toggle (Left/Right), seek rate constant (ms/cyl), return-jump toggle switch.
   - Main Stage: Large active Glow Card rendering trajectory. Supports interactive playback controls (Run, Step Forward, Play/Pause, Reset).
   - Trace Feed: Scrollable tabular log displaying current head position, target cylinder, delta distance, and running movement total.
   - Compare Matrix: Row of 6 compact Glow Cards (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK) comparing metrics concurrently.
3. **CPU Scheduling Studio:**
   - Process Table Editor: Dynamic row addition/removal for PIDs, Arrival, Burst, and Priority.
   - Time Slice Control: Interactive quantum slider for Round Robin.
   - Canvas Gantt Visualizer: Smooth color-coded process execution blocks with hovering execution window timestamps and idle period indicators.
4. **Page Replacement Studio:**
   - Virtual Reference Stream: Configurable page reference list and allocation frames.
   - Step Frame Matrix: Color-coded memory frame timeline (emerald highlight for Hits, soft rose for Faults).
   - Belady's Anomaly Visualizer: Side-by-side comparison demonstrating FIFO anomaly with 3 vs 4 frames on benchmark sequence.
5. **Deadlock Studio (Banker's Algorithm):**
   - Editable dynamic matrix grids: Allocation, Max Claim, Available Vectors, and calculated Need.
   - Step-by-step safety sequence animation highlighting which process claims work resources at each step.
   - Resource Request Sandbox: Test immediate grantability of ad-hoc resource vectors with rollback guarantees.
6. **System & Telemetry Drawer:**
   - Monospace Linux Diagnostics viewer displaying kernel details, CPU topology, and memory metrics from host.
   - Log Auditor with real-time severity breakdown.
   - Interactive Test Runner with live PASS/FAIL status indicators.

---

## 4. Accessibility, Motion & Interaction Contracts

1. **Reduced Motion (`prefers-reduced-motion: reduce`):**
   - All canvas animations immediately render to their completed state $t_{\text{final}}$.
   - Sine-squared breathing, line comet trailing, and pulse expansions are disabled.
   - Metric number count-ups immediately display their final formatted value.
2. **Keyboard Navigation & ARIA Compliance:**
   - Dropdown pill custom listboxes fully support `aria-expanded`, `role="listbox"`, and `role="option"`.
   - Full keyboard navigation: `Tab` to navigate, `Enter` / `Space` to activate, `Arrow Up` / `Arrow Down` to select options, `Escape` to close listboxes.
   - Visible `:focus-visible` double-ring styling on all interactive controls.
3. **Responsive Viewport Support:**
   - Fluid typography and component sizing from $360\text{px}$ mobile screens to $4\text{K}$ desktop monitors without clipping or horizontal overflow.
