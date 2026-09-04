const reduceMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;
let anime = null;

if (!reduceMotion) {
  try {
    anime = await import("https://cdn.jsdelivr.net/npm/animejs@4.5.0/+esm");
  } catch (error) {
    console.warn(
      "The motion library could not be loaded; showing the static composition.",
      error,
    );
  }
}

document.documentElement.dataset.motion = "ready";

if (anime) {
  const { animate, createTimeline, stagger } = anime;

  const intro = createTimeline({ defaults: { ease: "outExpo" } })
    .add(
      ".line-mask > span",
      { y: ["110%", "0%"], duration: 1050, delay: stagger(90) },
      80,
    )
    .add(
      ".motion-copy",
      { opacity: [0, 1], y: [14, 0], duration: 720, delay: stagger(100) },
      420,
    );

  if (document.body.dataset.architecture === "gateway") {
    intro
      .add(
        ".product-door",
        { opacity: [0, 1], x: [24, 0], duration: 820, delay: stagger(120) },
        260,
      )
      .add(
        ".door-rail",
        { scaleY: [0, 1], duration: 650, delay: stagger(100) },
        540,
      );

    animate(".format-runner", {
      x: () =>
        Math.max(0, document.querySelector(".dual-format").clientWidth * 0.89),
      duration: 2600,
      alternate: true,
      loop: true,
      ease: "inOutSine",
    });

    animate(".spine-runner", {
      y: [0, -88],
      duration: 2200,
      alternate: true,
      loop: true,
      ease: "inOutSine",
    });
  } else {
    intro.add(".output-proof", { opacity: [0, 1], duration: 900 }, 260);

    const startHorizontalSweep = (selector) => {
      const sweep = document.querySelector(selector);
      if (!sweep || !sweep.parentElement) return;
      animate(sweep, {
        x: [0, Math.max(0, sweep.parentElement.clientWidth - 1)],
        duration: 3400,
        alternate: true,
        loop: true,
        ease: "inOutSine",
      });
    };

    startHorizontalSweep(".proof-scan");
    startHorizontalSweep(".beat-wipe");

    const branchPath = document.querySelector(".branch-lines path");
    if (branchPath) {
      animate(branchPath, {
        strokeDashoffset: [1, 0],
        duration: 1200,
        autoplay: anime.onScroll({
          target: ".branch-intro",
          enter: "bottom 78%",
          leave: "top 20%",
          sync: false,
        }),
        ease: "inOutQuad",
      });
    }
  }
}

const tabs = [...document.querySelectorAll("[data-product]")];
const panels = [...document.querySelectorAll(".product-panel")];

function selectProduct(product) {
  tabs.forEach((tab) => {
    const selected = tab.dataset.product === product;
    tab.classList.toggle("is-selected", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });

  panels.forEach((panel) => {
    const selected = panel.id === `${product}-panel`;
    panel.hidden = !selected;
    panel.classList.toggle("is-visible", selected);
    if (selected && anime && !reduceMotion) {
      anime.animate(
        panel.querySelectorAll(".panel-copy > *, .product-panel > :last-child"),
        {
          opacity: [0, 1],
          y: [12, 0],
          duration: 520,
          delay: anime.stagger(55),
          ease: "outQuad",
        },
      );
    }
  });
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectProduct(tab.dataset.product));
  tab.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const next =
      tabs[
        (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
          tabs.length
      ];
    selectProduct(next.dataset.product);
    next.focus();
  });
});
