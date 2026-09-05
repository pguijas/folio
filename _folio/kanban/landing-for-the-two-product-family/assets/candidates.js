const root = document.documentElement
const button = document.querySelector("[data-theme-toggle]")
const stored = localStorage.getItem("folio-candidate-theme")
const preferredDark = window.matchMedia("(prefers-color-scheme: dark)").matches

if (stored === "dark" || (!stored && preferredDark)) {
  root.dataset.theme = "dark"
}

button?.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark"
  root.dataset.theme = next
  localStorage.setItem("folio-candidate-theme", next)
  button.setAttribute("aria-label", `Use ${next === "dark" ? "light" : "dark"} theme`)
})
