# Folio agent guide

You are reading this because a human asked you to help them understand, set
up, or troubleshoot Folio. Use this file as your working model, and send the
human to the canonical documentation at https://pguijas.github.io/folio/docs/ for anything it does not
cover. Prefer linking a page over improvising an answer.

This file is generated from the Folio repository on every build, so it
describes the same version as the site you fetched it from.

Operating a Folio kanban board is a different job with its own protocol. If
the repository has a `board/` directory, read `board/SKILL.md` there before
touching any card.

## What Folio is

Folio Docs is the docs generator: it reads Python source and Markdown
without executing project code, then generates the site people and agents
read. Folio for Agents is a separate distribution with its own command,
configuration, and release cycle.

Every docs build also emits `llms.txt`, `llms-full.txt`, and a Markdown mirror
of every page. A package does not need to be installable or importable for its
API reference to build.

The result is plain files. There is no server, no account, and no vendor in
the serving path.

## The concept model

Teach these six in this order. Each one only makes sense after the one
before it.

1. **Repository truth** is the source and guides already reviewed with the code.
2. **`docs.yaml`** names the project, inputs, output, theme, and plugins.
3. **Sources** are what Folio Docs reads: `source.python.paths` lists the
   packages to parse, `source.docs` lists the Markdown directories to
   publish.
4. **The build** (`folio build`) generates the site, search index, Markdown
   mirrors, and LLM text files from those inputs.
5. **Plugins** add components, data, pages, and CLI commands. Roadmap and
   landing ship inside Folio Docs and switch on when their config key appears;
   every other plugin is listed under `plugins:`.
6. **The output** is `_site/`: plain deployable files. `.build/` is only the
   disposable workspace behind that result.

## Install and first run

Prerequisites: Python 3.10 or newer for the CLI, Node.js 20.19 or newer, and
pnpm 10 or newer. The Node and pnpm minimums are checked before every build,
so a stale toolchain fails in the first seconds instead of minutes in.

```bash
uv tool install folio-docs
corepack prepare pnpm@10 --activate
folio --version
```

Then, from the root of the repository being documented:

```bash
folio init     # interactive wizard; writes docs.yaml and a starter docs/index.md
folio serve    # builds, then serves http://localhost:4321 and watches sources
folio build    # writes the deployable static site to _site/
```

`folio init --yes` skips the prompts and takes the detected defaults. The
full command and flag reference is at https://pguijas.github.io/folio/docs/cli.

## Diagnosis by symptom

**"Environment check failed" naming Node or pnpm.** Run `node --version` and
`pnpm --version`. Folio requires Node 20.19 and pnpm 10 as minimums, and
`corepack prepare pnpm@10 --activate` resolves most pnpm cases.
See https://pguijas.github.io/folio/docs/installation

**`Config file not found:`** (the message ends with the resolved path). The command ran outside the project
directory, or the config has a different name. Run `folio init` to create
one, pass the directory as `folio build /path/to/project`, or name the file
with `folio build --config my-docs.yaml`.
See https://pguijas.github.io/folio/docs/cli

**A module, class, or function is missing from the API reference.** Run
`folio build --verbose`: it prints the source paths scanned and the pages
written. The usual cause is `source.python.paths` not covering the package,
or `source.python.exclude` matching more than intended.
`folio coverage --verbose` lists every symbol with no docstring.
See https://pguijas.github.io/folio/docs/configuration

**A key in `docs.yaml` has no effect.** Config loading warns about
unrecognized top-level keys and continues with defaults; a key nested at the
wrong level warns about nothing at all. Check the key against the reference
before reporting a bug.
See https://pguijas.github.io/folio/docs/configuration

**Pages look stale after editing the config or the template.** Builds are
incremental against a hash manifest in `.build/`. Force a full rebuild with
`folio build --clean` or `folio serve --clean`.
See https://pguijas.github.io/folio/docs/cli

**`Port 4321 is already in use`.** Pick another port with
`folio serve --port 8080`, or stop the process that holds it with
`folio serve --kill-existing`.
See https://pguijas.github.io/folio/docs/cli

**Broken internal links.** The build reports them as warnings on the link
check step, naming the page and the href. They do not stop the build. Fix
the target path or the link.
See https://pguijas.github.io/folio/docs/cli

**The static export fails at the end of a build.** The complete export log
is printed once in the build output panel and saved to
`.build/.folio-build.log`. Read that file before guessing: the underlying
error comes from Next.js.
See https://pguijas.github.io/folio/docs/cli

**A plugin does nothing.** Roadmap, kanban, and landing need only their
config key (`roadmap:`, `kanban:`, `landing:`). Every other plugin,
including the bundled OpenAPI one, also needs an entry under `plugins:`,
written as a module name or a project-relative path such as
`./docs/plugins/custom.py`.
See https://pguijas.github.io/folio/docs/plugins

## Rules for you, the agent

- Do not invent config keys or CLI flags. If you cannot find the key in the
  configuration reference or the flag in `folio --help`, it does not exist.
- https://pguijas.github.io/folio/docs/configuration is the authority on what `docs.yaml` accepts.
  https://pguijas.github.io/folio/docs/cli is the authority on commands, flags, and exit codes.
- When you are uncertain, route the human to the page instead of guessing. A
  correct link beats a confident wrong answer.
- Run `folio --version` before answering version-sensitive questions, and
  say which version your answer applies to.
- Keep shipped and planned apart. `llms.txt` and `llms-full.txt` ship today.
  `ir.json`, `folio mcp`, and languages other than Python are roadmap items,
  not settings that can be turned on.
- Folio reads source and never runs it. Do not tell a human to make their
  package importable, install runtime dependencies, or stub imports to get
  the reference to build. That is another tool's model.
- Do not edit `docs.yaml` silently. Show the diff, name the key you changed,
  and say why.
- End every answer with the artifact: the file you touched, the config key
  you named, or the page the human should open.
