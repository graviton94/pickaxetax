// Scroll reveals and count-ups. Everything is fully visible without this file:
// the hidden start state exists only under html.motion, which is set here and
// never when the reader asked for reduced motion.

const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const root = document.documentElement;
if (!reduce && "IntersectionObserver" in window) root.classList.add("motion");

// "10.8", "148", "5,871,292,005", "16" -> animate to the same text, same decimals
function countUp(el) {
  const target = el.dataset.count;
  const n = parseFloat(target.replace(/,/g, ""));
  if (!isFinite(n)) return;
  const dec = (target.split(".")[1] || "").length;
  const grouped = target.includes(",");
  const loc = root.lang === "ko" ? "ko-KR" : "en-US";
  const show = (x) => (grouped ? Math.round(x).toLocaleString(loc) : x.toFixed(dec));
  const t0 = performance.now();
  const dur = Math.min(2200, 900 + 120 * String(Math.round(n)).length);
  const tick = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    el.textContent = show(n * (1 - Math.pow(1 - p, 4)));
    if (p < 1) requestAnimationFrame(tick); else el.textContent = target;
  };
  requestAnimationFrame(tick);
}

const io = root.classList.contains("motion")
  ? new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        e.target.classList.add("in");
        e.target.querySelectorAll("[data-count]").forEach(countUp);
        io.unobserve(e.target);
      }
    }, { threshold: 0.18, rootMargin: "0px 0px -6% 0px" })
  : null;

export function observe(scope = document) {
  if (!io) return;
  scope.querySelectorAll("[data-stagger]").forEach((g) => {
    [...g.children].forEach((c, i) => c.style.setProperty("--i", i));
  });
  scope.querySelectorAll("[data-reveal]:not(.in)").forEach((el) => io.observe(el));
}

observe();
