/**
 * Anime.js scroll reveals + hero entrance.
 * Adds html.js-motion only when ready so content never stays blank.
 */
(function () {
  document.documentElement.classList.add("js-motion");

  function heroEntrance() {
    if (typeof anime === "undefined") {
      document.documentElement.classList.remove("js-motion");
      return;
    }

    const brand = document.querySelector(".hero-brand");
    const line = document.querySelector(".hero-line");
    const ctas = document.querySelector(".hero-ctas");
    const eveningTitle = document.querySelector(".canvas-hero .evening-hero-title");
    const heroOrnament = document.querySelector(".canvas-hero .ornament");
    const heroKicker = document.querySelector(".canvas-hero .section-kicker");

    const timeline = anime.timeline({ easing: "easeOutCubic" });

    if (brand) {
      const lockupParts = brand.querySelectorAll(".brand-word, .brand-amp");
      if (heroOrnament) {
        timeline.add({
          targets: heroOrnament,
          opacity: [0, 1],
          scale: [0.7, 1],
          duration: 600,
        });
      }
      if (lockupParts.length) {
        brand.style.opacity = 1;
        timeline.add(
          {
            targets: lockupParts,
            opacity: [0, 1],
            translateY: [28, 0],
            duration: 800,
            delay: anime.stagger(120),
          },
          "-=200"
        );
      } else {
        timeline.add({
          targets: brand,
          opacity: [0, 1],
          translateY: [36, 0],
          duration: 900,
        });
      }
    } else if (eveningTitle) {
      const targets = [heroOrnament, heroKicker, eveningTitle].filter(Boolean);
      timeline.add({
        targets,
        opacity: [0, 1],
        translateY: [22, 0],
        duration: 750,
        delay: anime.stagger(100),
      });
    }

    if (line) {
      timeline.add(
        {
          targets: line,
          opacity: [0, 1],
          translateY: [20, 0],
          duration: 700,
        },
        "-=350"
      );
    }

    if (ctas) {
      timeline.add(
        {
          targets: ctas,
          opacity: [0, 1],
          translateY: [16, 0],
          duration: 600,
        },
        "-=400"
      );
    }
  }

  function setupReveals() {
    const nodes = document.querySelectorAll("[data-reveal]");
    if (!nodes.length) return;

    const show = (el) => {
      el.classList.add("is-visible");
      if (typeof anime !== "undefined") {
        anime({
          targets: el,
          opacity: [0, 1],
          translateY: [24, 0],
          duration: 750,
          easing: "easeOutCubic",
        });
      }
    };

    if (!("IntersectionObserver" in window) || typeof anime === "undefined") {
      document.documentElement.classList.remove("js-motion");
      nodes.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    // Safety: if nothing intersects within 1.2s, show everything
    const safety = setTimeout(() => {
      nodes.forEach((el) => {
        if (!el.classList.contains("is-visible")) show(el);
      });
    }, 1200);

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          show(entry.target);
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -5% 0px" }
    );

    nodes.forEach((el) => io.observe(el));

    window.addEventListener(
      "load",
      () => {
        clearTimeout(safety);
      },
      { once: true }
    );
  }

  function solidNav() {
    const nav = document.querySelector(".site-nav");
    if (!nav) return;
    const onScroll = () => {
      nav.classList.toggle("is-solid", window.scrollY > 40);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  document.addEventListener("DOMContentLoaded", () => {
    solidNav();
    heroEntrance();
    setupReveals();
  });
})();
