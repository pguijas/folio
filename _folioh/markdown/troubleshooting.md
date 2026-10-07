# Troubleshooting

*Match the message, then read the cause.*

Everything below is something the `folioh` binary prints. Match the message
first: the build names the step it failed on and the file it was reading, so
the message usually is the diagnosis.

## `Environment check failed`

The message names Node.js, pnpm, or both. `folioh build` and `folioh serve`
render through the bundled Next.js template, so both are checked before any
work starts and a stale toolchain fails in the first seconds instead of
minutes in:

```bash
node --version    # 20.19 or newer
pnpm --version    # 10 or newer
corepack enable pnpm && corepack prepare pnpm@10 --activate   # or: npm install -g pnpm@10
```

See [Installation](/docs/installation) for the prerequisites and the bundled
template.

## `Config file not found`

The message ends with the path Folioh looked for. The command ran outside the
project directory, or the config has a different name. Any of these resolves
it:

```bash
folioh init                              # write a docs.yaml here
folioh build /path/to/project            # the project directory as argument
folioh build --config my-docs.yaml       # a config under another name
```

## A module, class, or function is missing from the API reference

Run the build with `--verbose`: it prints the source roots it scanned and
every page it wrote.

```bash
folioh build --verbose
```

The usual cause is `source.<language>.paths` not covering the package, or
`source.<language>.exclude` matching more than intended. Check both against
[Configuration](/docs/configuration#source), and
[Languages](/docs/languages) for what each reader reads. A symbol that is present
but empty is a missing docstring, which `folioh coverage --verbose` lists one
by one.

## `Unknown config keys in docs.yaml`

Loading warns about every key a core section does not have (the top level,
`project`, `source`, `theme`, `template`, `llm`, `deploy`, `sidebar`, `search`
and `components`), names the nearest valid key when one is close, and
continues with defaults:
`Unknown project keys in docs.yaml: vesion (did you mean 'version'?)`. The
`landing`, `roadmap` and `openapi` sections are not checked in this release,
so a typo there is ignored without a warning. Check the key and its nesting
against [Configuration](/docs/configuration) before reporting a bug.

## Pages look stale after editing the config or the template

Builds are incremental against a hash manifest in `.build/`. The manifest
covers source hashes plus config, template, and generator fingerprints, so
most edits invalidate what they should. Force the full rebuild when one slips
through:

```bash
folioh build --clean
folioh serve --clean
```

## `Port 4321 is already in use`

The message names the port and the way out. Pick another one, or stop the
process holding it:

```bash
folioh serve --port 8080
folioh serve --kill-existing
```

## Broken internal links

The build reports them as warnings on the Links step, one line per link:
`<page>:<line> → <target>`. The page is the one holding the link, the target
is the link as it appears in the generated page (a relative link shows as its
resolved `/docs/` route), and the line counts in the generated
`.build/content/<page>.mdx`, not in the source file. They do not stop the
build. Relative links between guide pages (`./configuration`) survive the
static export; absolute paths into the site root do not always.

## The static export fails at the end of a build

The complete export log is printed once in the build output panel and saved
to `.build/.folioh-build.log`. Read that file before guessing: the underlying
error comes from Next.js and the log has the stack it printed.

## Something else

The [CLI Reference](/docs/cli) is the authority on commands, flags, and exit
codes, and [Configuration](/docs/configuration) on what `docs.yaml` accepts. When
neither explains it,
[open an issue](https://github.com/pguijas/folioh/issues) with the command you
ran and the output.
