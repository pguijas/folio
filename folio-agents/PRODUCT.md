# Folio for Agents

Folio for Agents is a meta-harness: a harness over the coding harnesses already
working in a repository. It gives them shared, durable context without replacing
or orchestrating them.

Its first product surface is the cardfile board and the protocol that travels
with it. Work state, acceptance criteria, trails, comments, and artifacts remain
plain Markdown under git. Board operations require no server, account, Node.js
runtime, or Docs build.

Version 0.1.0 is released independently as `folio-agents`. Once installed next
to the Folio CLI host, it contributes the `folio board` command group.

Its direction is a separate Agents track in the monorepo roadmap. The site is
built together, but Docs releases never determine Agents phases or versions.
