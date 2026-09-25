# Trust & Safety

*What a plugin can do on your machine, what Folio guarantees, and where those guarantees stop.*

<Callout type="warning" title="Not available in this release">
  Project plugins are not in Folio 0.3. They return with the sidecar protocol,
  and this page describes the trust decision that surface asks of you. The
  built-in integrations are part of the `folio` binary and need no such
  decision.
</Callout>

## A plugin is code you run

A Folio plugin is a program. `folio` starts it for the build and calls its hooks over stdio, so it runs with your environment variables, your filesystem permissions, and your network access. Anything your user account can read, write, or send, a configured plugin can read, write, or send.

The risk class is not new. Adding a plugin is the same trust decision you already make when you install a package and import it: you are choosing to execute someone else's code with your own privileges. Judge a plugin the way you judge a library, by its author, its source, and its release history, and not the way you judge a config file.

This is deliberate. A sidecar is its own process, but a sandbox that could stop a hostile plugin would also stop the useful ones from reading your source tree, writing pages, and adding CLI commands.

<Callout type="warning" title="Before you run folio in a repository you did not write">
  Read its `docs.yaml` first. Whatever it configures a build to start is the code you are about to execute.
</Callout>

Two situations where this matters most:

- **Cloning an unfamiliar repository.** Inspecting a project's docs config costs one `cat`; running a build inside it does not ask first.
- **CI.** A pull request that adds a plugin, or edits one already configured, runs that code in the job that builds the docs. Treat a docs build of an untrusted branch exactly like running its test suite.

## What you can do

- **Read `docs.yaml` before running `folio` in an unfamiliar repository.**
- **Prefer plugins you can read.** A plugin in the repository is in front of you. A published one has a source repository, a release history, and an author.
- **Pin what you install.** Version-pin a plugin like any other dependency and review the diff when you raise the pin.
- **Build untrusted branches without secrets.** Folio's own pull-request preview workflow splits the build in two: the job that runs pull-request code has read-only permissions and produces a static artifact, and only that artifact reaches the privileged job that deploys it. Any docs build of untrusted code wants that shape, or a container, or a throwaway environment.
- **Keep credentials out of `docs.yaml` and out of plugin code.** Static docs are published; anything a build embeds ships to readers.
- **Report what looks wrong.** A plugin nobody configured getting started is a bug in Folio. Report it privately through [GitHub Security Advisories](https://github.com/pguijas/folio/security/advisories/new) rather than a public issue.

## The boundary

Folio does not review, sandbox, or vet plugins. There is no signing, no permission model, no allowlist, and no restriction on what plugin code may do once you have configured it.

The `folio-plugin` GitHub topic described in [Publishing a plugin](./authoring#publishing-a-plugin) is a discovery convention, not an endorsement. A catalog built on it is on the roadmap, and a listing there would mean exactly one thing: a public repository carries a topic. It would not mean the code was read by anyone.

The trust decision stays with you. It is the same one you make for every other dependency in your environment, and Folio's job is to make sure you can see what you are deciding about.

The equivalent decision for frontend code is documented in [Theme Packages](../theming/theme-packages) and [Custom Templates](../theming/custom-templates).
