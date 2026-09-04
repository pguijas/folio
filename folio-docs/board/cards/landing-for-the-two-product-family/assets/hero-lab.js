const concepts = {
  "dual-canvas": {
    number: "01",
    name: "Dual canvas",
    note: "Literal product split",
    visual: `
      <div class="canvas-grid" aria-hidden="true"></div>
      <div class="source-token"><span>repository</span><strong>docs.yaml</strong></div>
      <div class="branch branch-docs" aria-hidden="true"></div>
      <div class="branch branch-agents" aria-hidden="true"></div>
      <article class="mini-surface docs-surface">
        <header><span class="window-dots">•••</span><span>Folio Docs</span><b>live</b></header>
        <div class="browser-layout"><i></i><div><strong>payments</strong><span>API reference</span><span>Guides</span></div></div>
      </article>
      <article class="mini-surface agents-surface future-surface">
        <header><span>AGENTS.md</span><b>soon</b></header>
        <div class="code-lines"><i></i><i></i><i></i><i></i></div>
        <footer>Folio for Agents</footer>
      </article>`,
  },
  "repository-orbit": {
    number: "02",
    name: "Repository orbit",
    note: "Organic system map",
    visual: `
      <div class="orbit-blob" aria-hidden="true"></div>
      <div class="orbit-ring ring-one" aria-hidden="true"></div>
      <div class="orbit-ring ring-two" aria-hidden="true"></div>
      <div class="repo-core"><span>one repository</span><strong>source<br>+ guides</strong></div>
      <div class="orbit-node node-docs"><span>HTML</span><strong>Folio Docs</strong><small>published</small></div>
      <div class="orbit-node node-agents future-surface"><span>MD</span><strong>Folio for Agents</strong><small>coming soon</small></div>
      <span class="orbit-caption">Two products · one source of truth</span>`,
  },
  "stacked-surfaces": {
    number: "03",
    name: "Stacked surfaces",
    note: "Product windows",
    visual: `
      <div class="stack-shadow stack-shadow-a" aria-hidden="true"></div>
      <article class="stack-panel stack-agents future-surface">
        <header><span>Folio for Agents</span><b>coming soon</b></header>
        <div class="agent-document"><strong>AGENTS.md</strong><i></i><i></i><i></i><span>board / artifacts / rules</span></div>
      </article>
      <article class="stack-panel stack-docs">
        <header><span class="window-dots">•••</span><b>docs.folio.dev</b></header>
        <div class="docs-document"><nav>Folio Docs</nav><main><small>API REFERENCE</small><strong>Build from source.</strong><i></i><i></i></main></div>
      </article>
      <div class="stack-config"><span>input</span><strong>docs.yaml</strong></div>`,
  },
  "split-sheet": {
    number: "04",
    name: "Split sheet",
    note: "HTML and Markdown as one page",
    visual: `
      <div class="sheet-rings" aria-hidden="true"></div>
      <article class="folio-sheet">
        <div class="sheet-half sheet-html"><span>Folio Docs</span><b>HTML</b><div class="page-lines"><i></i><i></i><i></i><i></i></div><small>people read</small></div>
        <div class="sheet-half sheet-md future-surface"><span>Folio for Agents</span><b>MD</b><pre># project\n## context\n- source\n- guides</pre><small>coming soon</small></div>
        <div class="sheet-fold" aria-hidden="true"></div>
      </article>
      <div class="sheet-source">docs.yaml <span>builds both</span></div>`,
  },
  "signal-rail": {
    number: "05",
    name: "Signal rail",
    note: "Engineering apparatus",
    visual: `
      <div class="rail-grid" aria-hidden="true"></div>
      <div class="rail-source"><span>01 / INPUT</span><strong>repository</strong><small>python · guides · yaml</small></div>
      <div class="main-rail" aria-hidden="true"><i></i><i></i><i></i></div>
      <article class="rail-output output-docs"><span>02A / ACTIVE</span><strong>Folio Docs</strong><div><b>HTML</b><b>search</b><b>API</b></div></article>
      <article class="rail-output output-agents future-surface"><span>02B / SOON</span><strong>Folio for Agents</strong><div><b>Markdown</b><b>context</b></div></article>
      <p class="rail-caption">ONE BUILD SIGNAL / TWO PRODUCT SURFACES</p>`,
  },
  "living-index": {
    number: "06",
    name: "Living index",
    note: "Repository-native files",
    visual: `
      <article class="index-window">
        <header><span class="window-dots">•••</span><b>folio / repository</b></header>
        <div class="index-body">
          <div class="file-tree"><span>▾ src</span><b>client.py</b><b>models.py</b><span>▾ docs</span><b>guides.md</b><strong>docs.yaml</strong></div>
          <div class="index-preview"><small>GENERATED SURFACES</small><div class="preview-row docs-row"><i>HTML</i><span><b>Folio Docs</b><em>site + reference</em></span></div><div class="preview-row future-surface"><i>MD</i><span><b>Folio for Agents</b><em>coming soon</em></span></div></div>
        </div>
      </article>
      <span class="index-stamp">READ REPOSITORY / NEVER RUN SOURCE</span>`,
  },
  "product-portals": {
    number: "07",
    name: "Product portals",
    note: "Architectural and calm",
    visual: `
      <div class="portal-ground" aria-hidden="true"></div>
      <div class="source-path"><span>repository truth</span></div>
      <article class="portal portal-docs"><span>01</span><div class="portal-inner"><small>Folio Docs</small><strong>HTML</strong><i></i><i></i></div><b>open</b></article>
      <article class="portal portal-agents future-surface"><span>02</span><div class="portal-inner"><small>Folio for Agents</small><strong>MD</strong><i></i><i></i></div><b>coming soon</b></article>
      <p class="portal-caption">Choose the surface.<br>The repository stays the same.</p>`,
  },
  "editorial-totem": {
    number: "08",
    name: "Editorial totem",
    note: "Abstract Folio identity",
    visual: `
      <div class="totem-field" aria-hidden="true"></div>
      <div class="totem-mark" aria-hidden="true"><span>F</span><span>O</span></div>
      <div class="totem-card totem-docs"><span>Folio Docs</span><strong>HTML</strong><small>01 / available</small></div>
      <div class="totem-card totem-agents future-surface"><span>Folio for Agents</span><strong>MD</strong><small>02 / coming soon</small></div>
      <div class="totem-rule" aria-hidden="true"></div>
      <p class="totem-caption">ONE REPOSITORY<br>TWO READING MODES</p>`,
  },
}

const copy = {
  docs: {
    overline: "Folio Docs",
    headline: "HTML for people, Markdown for agents.",
    description:
      "With one docs.yaml, Folio builds a complete documentation site from the Python source and guides already in your repository.",
    primary: "Get started",
    secondary: "View documentation",
    command: "$ uv tool install folio",
  },
  agents: {
    overline: "Folio for Agents · Coming soon",
    headline: "One shared project memory for every coding agent.",
    description:
      "Folio for Agents will give the coding tools already in your repository one shared context, board, and set of durable artifacts.",
    primary: "Follow development",
    secondary: "Return to Folio Docs",
    command: "Roadmap · not yet available",
  },
}

const root = document.querySelector("[data-hero-root]")

if (root) {
  const key = document.body.dataset.concept || "dual-canvas"
  const concept = concepts[key] || concepts["dual-canvas"]
  document.title = `Folio hero ${concept.number}: ${concept.name}`
  root.innerHTML = `
    <a class="skip-link" href="#hero-copy">Skip to hero copy</a>
    <div class="prototype-meta">
      <span>Hero study ${concept.number} / 08</span>
      <strong>${concept.name}</strong>
      <button class="theme-control" type="button" aria-label="Toggle color theme">◐</button>
    </div>
    <main class="hero-frame" data-product="docs">
      <section class="hero-layout" aria-labelledby="hero-title">
        <div class="visual-column">
          <div class="visual-stage variant-${key}" aria-label="${concept.name}: Folio Docs and Folio for Agents visual concept">
            ${concept.visual}
          </div>
          <p class="concept-note"><span>${concept.number}</span>${concept.note}</p>
        </div>
        <div class="copy-column" id="hero-copy">
          <div class="product-switcher" role="tablist" aria-label="Choose a Folio product">
            <button type="button" role="tab" aria-selected="true" data-product-choice="docs">Folio Docs</button>
            <button type="button" role="tab" aria-selected="false" data-product-choice="agents">Folio for Agents <small>Coming soon</small></button>
          </div>
          <p class="overline" data-copy="overline"></p>
          <h1 id="hero-title" data-copy="headline"></h1>
          <p class="description" data-copy="description"></p>
          <div class="hero-actions">
            <a class="button primary" data-copy="primary" href="https://pguijas.github.io/folio/docs/quickstart/"></a>
            <a class="button secondary" data-copy="secondary" href="https://pguijas.github.io/folio/docs/"></a>
          </div>
          <div class="command" data-copy="command"></div>
        </div>
      </section>
    </main>`

  const frame = root.querySelector(".hero-frame")
  const choices = [...root.querySelectorAll("[data-product-choice]")]

  function setProduct(product) {
    const values = copy[product]
    frame.dataset.product = product
    choices.forEach((choice) => {
      choice.setAttribute(
        "aria-selected",
        String(choice.dataset.productChoice === product)
      )
    })
    Object.entries(values).forEach(([field, value]) => {
      root.querySelector(`[data-copy="${field}"]`).textContent = value
    })
    const links = root.querySelectorAll(".hero-actions a")
    if (product === "agents") {
      links[0].href = "https://github.com/pguijas/folio"
      links[1].href = "#"
      links[1].addEventListener("click", returnToDocs, { once: true })
    } else {
      links[0].href = "https://pguijas.github.io/folio/docs/quickstart/"
      links[1].href = "https://pguijas.github.io/folio/docs/"
    }
  }

  function returnToDocs(event) {
    event.preventDefault()
    setProduct("docs")
  }

  choices.forEach((choice) => {
    choice.addEventListener("click", () => setProduct(choice.dataset.productChoice))
  })
  setProduct("docs")
}

document.querySelectorAll(".theme-control").forEach((control) => {
  control.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark"
    document.documentElement.dataset.theme = next
  })
})
