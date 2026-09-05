# Trust & Safety

*What a plugin can do on your machine, what Folio guarantees, and where those guarantees stop.*

## A plugin is code you run

A Folio plugin is Python. Folio imports it and calls its hooks inside your build, in the same interpreter process as Folio itself. It runs with your environment variables, your filesystem permissions, and your network access. Anything your user account can read, write, or send, a listed plugin can read, write, or send.

The risk class is not new. Adding a plugin is the same trust decision you already make when you install a package and import it: you are choosing to execute someone else's code with your own privileges. Judge a plugin the way you judge a library, by its author, its source, and its release history, and not the way you judge a config file.

This is deliberate. Plugins get the whole Python process because that is what makes the extension surface worth having: the first-party roadmap, kanban, landing, and OpenAPI plugins go through the exact same hooks a third-party plugin uses. A sandbox that could stop a hostile plugin would also stop the useful ones from reading your source tree, writing pages, and adding CLI commands.

## Plugins load before your command runs

This is the sharpest edge in the system.

Project plugins listed under `plugins:` in `./docs.yaml` load when the CLI starts, not when a build starts. Typer finalizes its command table while `folio.cli` is imported, before any argument is parsed, so a plugin that wants to contribute a command has to be imported by then. Folio therefore reads `docs.yaml` from the current working directory at import time and loads every plugin it lists.

The consequence: running **any** `folio` command from a directory whose
`docs.yaml` lists plugins executes those plugins' module-level code. `folio
--help` is enough. So is a typo that never reaches a command.

**Before you run folio in a repository you did not write**

  Read its `docs.yaml` first. The `plugins:` list is the code you are about to execute, and a file-path entry such as `./plugins/build_hooks.py` is right there in the tree for you to read.

Two situations where this matters most:

- **Cloning an unfamiliar repository.** Inspecting a project's docs config costs one `cat`; running `folio --help` inside it does not ask first.
- **CI.** A pull request that adds a `plugins:` entry, or edits a file-path plugin already listed, runs that code in the job that builds the docs. Treat a docs build of an untrusted branch exactly like running its test suite.

A plugin that fails while the CLI is starting is reported as a warning and skipped, so a broken plugin never takes down the CLI. Being skipped after a failure is not containment: by then the module-level code has already run.

## What Folio does guarantee

Four properties are enforced in code, and each one is a real load-time or failure-time boundary:

- **Installing a build plugin never activates it.** A `folio-docs` build-plugin
  entry point is inert until its name appears in `plugins:`. The separate
  `folio.cli` group is reserved for installed Folio products that intentionally
  add commands to the shared CLI; loading one does not activate build hooks.
- **File-path plugins cannot resolve outside the project directory.** A `./plugins/x.py` entry is resolved against the project directory and rejected when the resolved path lands outside it. Because the path is fully resolved first, a symlink pointing out of the tree is rejected too. Loading reports the refusal as a `RuntimeError` naming the plugin, with the original `ValueError` as its cause.
- **A plugin built for another API major refuses to load.** A plugin may declare `FOLIO_PLUGIN_API`; if its major differs from the host's, it is refused instead of running hooks it was not written for. The declaration is optional, so an undeclared plugin loads without this check.
- **Hook failures are isolated and attributed.** Folio dispatches every hook one implementation at a time rather than as a single pluggy broadcast, so a failure names the plugin under the string you wrote in `plugins:`. Config and registry hooks fail the build; `config_keys`, `emit_assets`, `post_build`, and `register_cli` warn and skip. `emit_assets` also runs under a rollback guard: when an implementation raises, the routes it registered are restored to the pre-hook snapshot, so a route with no page behind it cannot pass link checking and then 404 on the deployed site. The full policy table is in [Writing Plugins](./authoring#hook-failure-policies).

None of these is a security boundary around a running plugin. They constrain *what gets loaded* and *how a failure is contained*, not what a loaded plugin may do.

## What you can do

- **Read `docs.yaml` before running `folio` in an unfamiliar repository.** The `plugins:` list is the entire build-plugin surface.
- **Prefer plugins you can read.** A file-path plugin is in the repository in front of you. An entry-point plugin is a published distribution with a source repository, a release history, and an author.
- **Pin the distribution.** Version-pin a plugin like any other dependency and review the diff when you raise the pin.
- **Build untrusted branches without secrets.** Folio's own pull-request preview workflow splits the build in two: the job that runs pull-request code has read-only permissions and produces a static artifact, and only that artifact reaches the privileged job that deploys it. Any docs build of untrusted code wants that shape, or a container, or a throwaway environment.
- **Keep credentials out of `docs.yaml` and out of plugin code.** Static docs are published; anything a build embeds ships to readers.
- **Report what looks wrong.** A plugin nobody listed getting loaded, or a file-path plugin resolving outside the project directory, is a bug in Folio. See [SECURITY.md](https://github.com/pguijas/folio/blob/main/SECURITY).

## The boundary

Folio does not review, sandbox, or vet plugins. There is no signing, no permission model, no allowlist, and no restriction on what plugin code may do once you have listed it.

The `folio-plugin` GitHub topic described in [Publishing a plugin](./authoring#publishing-a-plugin) is a discovery convention, not an endorsement. A catalog built on it is on the roadmap, and a listing there would mean exactly one thing: a public repository carries a topic. It would not mean the code was read by anyone.

The trust decision stays with you. It is the same one you make for every other dependency in your environment, and Folio's job is to make sure you can see what you are deciding about.

The equivalent decision for frontend code is documented in [Theme Packages](../theming/theme-packages) and [Custom Templates](../theming/custom-templates).
