/* ===========================================================================
   AttentionLab — supplemental client-side animations.
   NOTE: Streamlit sandboxes injected <script> tags, so this is treated as a
   progressive enhancement. The core reveal animations are pure CSS and always
   work; this file simply adds extras when the browser allows it.
   =========================================================================== */
(function () {
    "use strict";

    // ---- Scroll-triggered reveal (re-runs as Streamlit re-renders) --------
    function wireReveals() {
        if (!("IntersectionObserver" in window)) return;
        const io = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        e.target.style.animationPlayState = "running";
                        io.unobserve(e.target);
                    }
                });
            },
            { threshold: 0.12 }
        );
        document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
    }

    // ---- Typewriter effect for any [data-typewriter] element --------------
    function wireTypewriter() {
        document.querySelectorAll("[data-typewriter]").forEach((el) => {
            if (el.dataset.twDone) return;
            const full = el.textContent.trim();
            el.dataset.twDone = "1";
            el.textContent = "";
            let i = 0;
            const tick = () => {
                el.textContent = full.slice(0, i++);
                if (i <= full.length) requestAnimationFrame(() => setTimeout(tick, 28));
            };
            tick();
        });
    }

    function boot() {
        try {
            wireReveals();
            wireTypewriter();
        } catch (err) {
            /* best-effort only */
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
    // Streamlit swaps DOM on rerun — poll briefly to re-wire.
    let n = 0;
    const t = setInterval(() => {
        boot();
        if (++n > 12) clearInterval(t);
    }, 700);
})();
