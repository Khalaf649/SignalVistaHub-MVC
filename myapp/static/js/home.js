const cardRows = document.querySelectorAll(".card-row");
function revealCards() {
  const triggerBottom = window.innerHeight * 0.85;
  cardRows.forEach((row) => {
    if (row.getBoundingClientRect().top < triggerBottom) {
      row.classList.add("visible");
    }
  });
}
window.addEventListener("scroll", revealCards);
window.addEventListener("load", revealCards);
