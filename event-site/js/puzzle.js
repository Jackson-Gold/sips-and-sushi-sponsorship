/**
 * 3×3 sliding puzzle. On solve, unlocks gated invite/sponsor panels.
 *
 * Markup:
 *   <div class="puzzle-board" data-puzzle data-image="assets/images/puzzle.jpg"
 *        data-unlock="#invite-gate"></div>
 */
(function () {
  const SIZE = 3;
  const N = SIZE * SIZE;

  function indexToPos(i) {
    return { row: Math.floor(i / SIZE), col: i % SIZE };
  }

  function neighbors(blank) {
    const { row, col } = indexToPos(blank);
    const out = [];
    if (row > 0) out.push(blank - SIZE);
    if (row < SIZE - 1) out.push(blank + SIZE);
    if (col > 0) out.push(blank - 1);
    if (col < SIZE - 1) out.push(blank + 1);
    return out;
  }

  function isSolved(order) {
    for (let i = 0; i < N - 1; i++) {
      if (order[i] !== i) return false;
    }
    return order[N - 1] === N - 1;
  }

  /** Fisher–Yates shuffle that remains solvable (odd permutation for blank on last). */
  function shuffleSolvable() {
    const order = Array.from({ length: N }, (_, i) => i);
    // Move blank via legal slides so solvability is guaranteed.
    let blank = N - 1;
    for (let i = 0; i < 80; i++) {
      const opts = neighbors(blank);
      const pick = opts[Math.floor(Math.random() * opts.length)];
      order[blank] = order[pick];
      order[pick] = N - 1;
      blank = pick;
    }
    if (isSolved(order)) {
      // One more move if we landed solved.
      const opts = neighbors(blank);
      const pick = opts[0];
      order[blank] = order[pick];
      order[pick] = N - 1;
    }
    return order;
  }

  function unlock(targetSel) {
    const gate = document.querySelector(targetSel);
    if (!gate) return;
    gate.classList.remove("gate-locked");
    gate.classList.add("gate-unlocked");

    const panel = gate.querySelector(".form-panel, .unlock-cta");
    if (typeof anime !== "undefined" && panel) {
      anime({
        targets: gate.querySelectorAll(".unlock-cta, .form-panel"),
        opacity: [0, 1],
        translateY: [18, 0],
        duration: 700,
        delay: anime.stagger(80),
        easing: "easeOutCubic",
      });
    }

    const live = document.getElementById("puzzle-live");
    if (live) live.textContent = "Puzzle solved. Invite request unlocked.";

    const btn = gate.querySelector(".unlock-cta .btn, #request-invite-btn");
    if (btn) {
      btn.removeAttribute("disabled");
      btn.removeAttribute("aria-disabled");
      btn.focus({ preventScroll: true });
    }
  }

  function initBoard(board) {
    const image = board.getAttribute("data-image") || "assets/images/puzzle.jpg";
    const unlockSel = board.getAttribute("data-unlock") || "#invite-gate";
    let order = shuffleSolvable();
    let solved = false;

    board.setAttribute("role", "grid");
    board.setAttribute("aria-label", "Sliding picture puzzle");

    function blankIndex() {
      return order.indexOf(N - 1);
    }

    function render() {
      board.innerHTML = "";
      order.forEach((tileId, pos) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "puzzle-tile";
        btn.setAttribute("role", "gridcell");

        if (tileId === N - 1) {
          btn.classList.add("is-blank");
          btn.setAttribute("aria-label", "Empty space");
          btn.tabIndex = -1;
        } else {
          const { row, col } = indexToPos(tileId);
          btn.style.backgroundImage = `url("${image}")`;
          btn.style.backgroundPosition = `${(col / (SIZE - 1)) * 100}% ${(row / (SIZE - 1)) * 100}%`;
          btn.setAttribute("aria-label", `Tile ${tileId + 1}`);
          btn.addEventListener("click", () => tryMove(pos));
        }
        board.appendChild(btn);
      });
    }

    function tryMove(pos) {
      if (solved) return;
      const blank = blankIndex();
      if (!neighbors(blank).includes(pos)) return;
      order[blank] = order[pos];
      order[pos] = N - 1;
      render();

      if (isSolved(order)) {
        solved = true;
        const status = document.querySelector(".puzzle-status");
        if (status) {
          status.textContent = "Solved — welcome.";
          status.classList.add("is-solved");
        }
        if (typeof anime !== "undefined") {
          anime({
            targets: board,
            scale: [1, 1.02, 1],
            duration: 500,
            easing: "easeInOutQuad",
          });
        }
        unlock(unlockSel);
      }
    }

    board.addEventListener("keydown", (e) => {
      if (solved) return;
      const blank = blankIndex();
      const { row, col } = indexToPos(blank);
      let target = null;
      if (e.key === "ArrowUp" && row < SIZE - 1) target = blank + SIZE;
      if (e.key === "ArrowDown" && row > 0) target = blank - SIZE;
      if (e.key === "ArrowLeft" && col < SIZE - 1) target = blank + 1;
      if (e.key === "ArrowRight" && col > 0) target = blank - 1;
      if (target != null) {
        e.preventDefault();
        tryMove(target);
      }
    });

    // Make board focusable for keyboard
    board.tabIndex = 0;
    render();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-puzzle]").forEach(initBoard);
  });
})();
