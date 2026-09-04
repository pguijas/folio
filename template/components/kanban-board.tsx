"use client"

import {
  Fragment,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react"

import { kanbanColumns } from "@/lib/kanban-data"
import { cn } from "@/lib/utils"

/* ------------------------------------------------------------------ */
/* Card contract                                                        */
/*                                                                      */
/* Local superset of every shape lib/kanban-data.ts has exported.       */
/* Extended fields are optional because data from older folio builds    */
/* only carried title/description/tags/assignee/link; every access to   */
/* newer fields is guarded.                                             */
/* ------------------------------------------------------------------ */

interface KanbanArtifact {
  kind: string
  target: string
  /** The target as the author wrote it: the bare name for a sibling
   * derived from the card's directory, a fuller path only where one was
   * written. Absent on data from builds that predate derivation, which
   * keep rendering the resolved target. */
  display?: string
  label: string
  href: string
}

interface KanbanCriterion {
  text: string
  done: boolean
}

interface KanbanComment {
  date: string
  actor: string
  text: string
}

interface KanbanTrailEntry {
  date: string
  actor: string
  ref: string
  note: string
  /** Resolved at build time from `project.repo`: a commit sha or `PR #n`
   * becomes the URL it already named. Absent on boards built before this,
   * and empty when no repo is configured, so the ref falls back to text. */
  href?: string
}

interface KanbanCard {
  id?: string
  title: string
  description: string
  tags: string[]
  assignee: string[]
  /** Free-vocabulary kind of work (`bug`, `plan`, `feature`…); the types
   * that exist are the types cards use, exactly like milestone. */
  type?: string
  /** Closed scale — S | M | L | XL, normalized uppercase at build time. */
  size?: string
  /** Resolved at build time from board.yaml's `icons:` tag map; empty when
   * no tag is mapped. `iconTag` names the tag that brought the icon. */
  icon?: string
  iconTag?: string
  /** Where the work lives: a branch, `repo#branch`, a URL — free vocabulary
   * like `type`. */
  source?: string
  link: string
  priority?: string
  parent?: string
  blocked_by?: string[]
  created?: string
  milestone?: string
  artifacts?: KanbanArtifact[]
  criteria?: KanbanCriterion[]
  trail?: KanbanTrailEntry[]
  comments?: KanbanComment[]
  /** The roadmap step this card's milestone names, resolved at build time
   * from the roadmap section of the same docs.yaml. `phase` is the anchor,
   * `phaseTitle` the human name. Absent on boards built before this, and on
   * milestones no roadmap phase claims. */
  phase?: string
  phaseTitle?: string
  /** Where this card lives, as a project-relative path. A path, never a URL:
   * the board is operated locally, through the CLI and an editor, so "where
   * do I change this" is answered with the path rather than a link out to
   * whoever happens to host the repository. Empty on a board that is not a
   * card directory. */
  file?: string
}

interface KanbanColumn {
  id: string
  title: string
  limit: number | null
  cards: KanbanCard[]
}

/* Cards are addressed by a stable uid, never by their position. Position
   is a property of the *filtered* render, so an index-addressed move
   moves whichever card happens to sit at that index. The uid is the card's
   own id (the id the CLI takes), and a fallback slug exists only for data
   built before every board became a cardfile. */
type IdentifiedCard = KanbanCard & { uid: string }

interface BoardColumn {
  id: string
  title: string
  limit: number | null
  cards: IdentifiedCard[]
}

function identify(columns: KanbanColumn[]): BoardColumn[] {
  const seen = new Map<string, number>()
  return columns.map((column) => ({
    ...column,
    cards: column.cards.map((card) => {
      const base = card.id || `${column.id}:${card.title}`
      const taken = seen.get(base) ?? 0
      seen.set(base, taken + 1)
      return { ...card, uid: taken === 0 ? base : `${base}#${taken}` }
    }),
  }))
}

/* ------------------------------------------------------------------ */
/* Local persistence                                                    */
/*                                                                      */
/* The card files in git stay the source of truth. Drag-and-drop        */
/* changes are an overlay saved in localStorage as a map of card uid to */
/* the column it was dragged into, together with the column it came     */
/* from. The `from` column is the staleness check: an entry applies     */
/* only while the committed board still has that card where the entry   */
/* says it was, so editing an unrelated card no longer throws the whole */
/* overlay away, and a card the repo has since moved is left where the  */
/* repo put it. The export button closes the loop: it exports `folio    */
/* kanban move` commands — the browser captures intent, it never writes */
/* card files.                                                          */
/* ------------------------------------------------------------------ */

interface OverlayEntry {
  from: string
  to: string
}

type Overlay = Record<string, OverlayEntry>

function sourceHash(text: string) {
  let hash = 0
  for (let i = 0; i < text.length; i++) {
    hash = (Math.imul(31, hash) + text.charCodeAt(i)) | 0
  }
  return hash.toString(36)
}

function cloneBoard(board: BoardColumn[]): BoardColumn[] {
  return board.map((column) => ({ ...column, cards: [...column.cards] }))
}

function committedColumns(baseline: BoardColumn[]) {
  const map = new Map<string, string>()
  for (const column of baseline) {
    for (const card of column.cards) {
      map.set(card.uid, column.id)
    }
  }
  return map
}

function overlayOf(baseline: BoardColumn[], board: BoardColumn[]): Overlay {
  const committed = committedColumns(baseline)
  const overlay: Overlay = {}
  for (const column of board) {
    for (const card of column.cards) {
      const from = committed.get(card.uid)
      if (from !== undefined && from !== column.id) {
        overlay[card.uid] = { from, to: column.id }
      }
    }
  }
  return overlay
}

function applyOverlay(baseline: BoardColumn[], overlay: Overlay) {
  const board = cloneBoard(baseline)
  let applied = 0
  for (const [uid, entry] of Object.entries(overlay)) {
    if (
      !entry ||
      typeof entry.from !== "string" ||
      typeof entry.to !== "string"
    ) {
      continue
    }
    const from = board.findIndex((column) => column.id === entry.from)
    const to = board.findIndex((column) => column.id === entry.to)
    if (from < 0 || to < 0 || from === to) {
      continue
    }
    const at = board[from].cards.findIndex((card) => card.uid === uid)
    if (at < 0) {
      // The committed board no longer has this card here: the entry is
      // stale and the repository wins.
      continue
    }
    board[to].cards.push(board[from].cards.splice(at, 1)[0])
    applied++
  }
  return { board, applied }
}

/* The board is owned by the card files on disk, so the browser captures
   intent: one `folio kanban move` command per card whose column drifted from
   the committed baseline, to review and run in the repo. */
function boardToMoveCommands(baseline: BoardColumn[], board: BoardColumn[]) {
  const committed = committedColumns(baseline)
  const lines = ["# review, then run"]
  for (const column of board) {
    for (const card of column.cards) {
      if (!card.id) {
        continue
      }
      const from = committed.get(card.uid)
      if (from !== undefined && from !== column.id) {
        lines.push(`folio kanban move ${card.id} ${column.id}`)
      }
    }
  }
  return lines.join("\n") + "\n"
}

/* ------------------------------------------------------------------ */
/* The filter is one expression                                         */
/*                                                                      */
/* The input's value is the whole filter state. There is no second       */
/* store of committed facets beside it, because two stores of the same   */
/* thing is two answers to "what is filtered" — the old pair could       */
/* disagree, and a menu could produce `-tag:spec tag:spec` in one click. */
/*                                                                      */
/* The vocabulary is not invented: every field name below is a key that  */
/* already appears in board/cards/<id>.md frontmatter, plus `status`,    */
/* which is the column a card sits in and is spelled the same way        */
/* `folio kanban move <id> in-review` spells it. That is what lets the   */
/* whole language be taught in three lines, to a person or an agent.     */
/*                                                                      */
/*   whitespace is AND     tag:spec priority:high                        */
/*   comma is OR           tag:spec,launch                               */
/*   - excludes            -tag:spec                                     */
/*   quotes are exact      tag:"core"                                    */
/*   none / any            milestone:none, artifact:any                  */
/*                                                                      */
/* The parser has no failure mode. An unknown field name is not an       */
/* error, it is text — which is what keeps a pasted URL or a typed       */
/* "TODO:" harmless. A field with no value yet is dropped, so the board  */
/* does not blink empty between the colon and the first character.       */
/* ------------------------------------------------------------------ */

interface FilterField {
  key: string
  label: string
  aliases?: string[]
  /** Ordered comparison (`created:>2026-07-01`) is only meaningful on a
   * field whose values sort, and only ISO dates do here. */
  ordered?: boolean
  values: (card: KanbanCard, columnId: string, columnTitle: string) => string[]
}

const FILTER_FIELDS: FilterField[] = [
  {
    key: "status",
    label: "Status",
    // Both spellings: the column id as board.yaml declares it, and the
    // title as the column header prints it, so `status:in-review` and
    // `status:"in review"` both work rather than only the one the reader
    // cannot see.
    values: (_card, columnId, columnTitle) => [
      columnId,
      columnTitle.toLowerCase(),
      columnTitle.toLowerCase().replace(/\s+/g, "-"),
    ],
  },
  {
    key: "milestone",
    label: "Milestone",
    values: (card) => (card.milestone ? [card.milestone] : []),
  },
  {
    key: "type",
    label: "Type",
    values: (card) => (card.type ? [card.type] : []),
  },
  {
    key: "tag",
    label: "Tag",
    aliases: ["tags"],
    values: (card) => card.tags ?? [],
  },
  {
    key: "priority",
    label: "Priority",
    values: (card) => (card.priority ? [card.priority] : []),
  },
  {
    key: "size",
    label: "Size",
    values: (card) => (card.size ? [card.size] : []),
  },
  {
    key: "assignee",
    label: "Assignee",
    values: (card) => card.assignee ?? [],
  },
  {
    key: "source",
    label: "Source",
    values: (card) => (card.source ? [card.source] : []),
  },
  { key: "id", label: "Id", values: (card) => (card.id ? [card.id] : []) },
  {
    key: "parent",
    label: "Parent",
    values: (card) => (card.parent ? [card.parent] : []),
  },
  {
    key: "blocked_by",
    label: "Blocked by",
    aliases: ["blocked-by"],
    values: (card) => card.blocked_by ?? [],
  },
  {
    key: "created",
    label: "Created",
    ordered: true,
    values: (card) => (card.created ? [card.created] : []),
  },
  {
    key: "artifact",
    label: "Artifact",
    aliases: ["artifacts"],
    values: (card) =>
      (card.artifacts ?? []).flatMap((artifact) => [
        artifact.kind,
        artifact.target,
      ]),
  },
]

const FIELD_BY_NAME = new Map<string, FilterField>()
for (const field of FILTER_FIELDS) {
  FIELD_BY_NAME.set(field.key, field)
  for (const alias of field.aliases ?? []) {
    FIELD_BY_NAME.set(alias, field)
  }
}

/** The four that shipped as URL parameters before the expression existed.
 * Only these are folded in from the address bar: reading every field name
 * as a parameter would mean a page opened with someone else's `?id=42`
 * silently filters itself to nothing. */
const LEGACY_PARAMS = ["milestone", "tag", "priority", "assignee"]

type CompareOp = ">" | ">=" | "<" | "<="

interface QueryAlternative {
  text: string
  exact: boolean
  op?: CompareOp
}

interface QueryTerm {
  negate: boolean
  /** The resolved field, or null for a bare-text term. */
  field: FilterField | null
  alternatives: QueryAlternative[]
  /** Set when the token was shaped like `name:value` but `name` is not a
   * field, so the whole token was searched as text. `owner:pedro` means
   * that on purpose; `tagg:spec` is a typo, and the two are
   * indistinguishable until the board comes back empty and has to explain
   * itself. */
  unknownField?: string
}

const FULL_ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

/** Split on whitespace, with double quotes binding.
 *
 * A quote only binds when it has a partner later in the input. Every
 * quoted value is unterminated for as long as it is being typed, and a
 * quote that binds to the end of the line swallows every term after it —
 * so `tag:"spec milestone:0.7` became one term asking for a tag literally
 * called `spec milestone:0.7`, silently destroying a term the reader had
 * already finished. */
function tokenizeQuery(input: string): string[] {
  const tokens: string[] = []
  let current = ""
  let quoted = false
  for (let index = 0; index < input.length; index++) {
    const character = input[index]
    if (character === '"') {
      if (!quoted && input.indexOf('"', index + 1) === -1) {
        current += character
        continue
      }
      quoted = !quoted
      current += character
      continue
    }
    if (!quoted && /\s/.test(character)) {
      if (current) {
        tokens.push(current)
      }
      current = ""
      continue
    }
    current += character
  }
  if (current) {
    tokens.push(current)
  }
  return tokens
}

function firstColonOutsideQuotes(token: string): number {
  let quoted = false
  for (let index = 0; index < token.length; index++) {
    const character = token[index]
    if (character === '"') {
      quoted = !quoted
    } else if (character === ":" && !quoted) {
      return index
    }
  }
  return -1
}

/* The comma is the or, and a comma inside quotes is a comma. Splitting on
   every comma would break `tag:"a,b"`; not splitting when the value opens
   with one broke every list whose first value is quoted — `tag:"core",spec`
   asked for a tag literally called `core","spec` and answered nothing,
   while `tag:spec,"core"` answered correctly. Two documented rules that
   compose in one order and not the other are not a rule, they are a bug.
   Same quote-aware scan as `firstColonOutsideQuotes`, for the same reason. */
function splitAlternatives(raw: string): string[] {
  const parts: string[] = []
  let current = ""
  let quoted = false
  for (const character of raw) {
    if (character === '"') {
      quoted = !quoted
      current += character
      continue
    }
    if (character === "," && !quoted) {
      parts.push(current)
      current = ""
      continue
    }
    current += character
  }
  parts.push(current)
  return parts
}

function readAlternative(
  raw: string,
  ordered: boolean
): QueryAlternative | null {
  let text = raw
  let op: CompareOp | undefined
  if (ordered) {
    const match = text.match(/^(>=|<=|>|<)/)
    if (match) {
      op = match[1] as CompareOp
      text = text.slice(match[1].length)
    }
  }
  const exact = text.startsWith('"') && text.endsWith('"') && text.length >= 2
  if (exact) {
    text = text.slice(1, -1)
  } else {
    text = text.replace(/"/g, "")
  }
  if (!text) {
    return null
  }
  // An ordered comparison against a half-typed or unpadded date is worse
  // than no comparison: `created:>2026-8-1` compares as a string and
  // silently answers about the wrong days. Until the date is a full ISO
  // one, the alternative is not asked.
  if (op && !FULL_ISO_DATE.test(text)) {
    return null
  }
  return { text: text.toLowerCase(), exact, op }
}

/** Parse an expression into terms. Never throws; never reports an error. */
function parseQuery(source: string): QueryTerm[] {
  // A full-width colon arrives from an IME or from autocorrect and looks
  // identical on screen, so it is the same character here.
  const tokens = tokenizeQuery(source.replace(/：/g, ":"))
  const terms: QueryTerm[] = []
  for (const token of tokens) {
    let body = token
    let negate = false
    // `-` excludes, but only in front of a real field. A bare `-word` is
    // text: this board's ids are full of hyphens, and `-technical-plan`
    // meaning "everything except" would invert what was asked — and would
    // change what every already-shared `?q=` link means.
    if (body.startsWith("-")) {
      const rest = body.slice(1)
      const colon = firstColonOutsideQuotes(rest)
      if (colon > 0 && FIELD_BY_NAME.has(rest.slice(0, colon).toLowerCase())) {
        negate = true
        body = rest
      }
    }

    // A token that opens with a quote is text, always. That single rule is
    // the escape hatch for searching anything shaped like a field.
    const colon = body.startsWith('"') ? -1 : firstColonOutsideQuotes(body)
    const field =
      colon > 0
        ? (FIELD_BY_NAME.get(body.slice(0, colon).toLowerCase()) ?? null)
        : null

    if (!field) {
      const alternative = readAlternative(body, false)
      if (alternative) {
        // `colon > 0` means it was spelled like a field and is not one.
        const named = colon > 0 ? body.slice(0, colon) : ""
        terms.push({
          negate: false,
          field: null,
          alternatives: [alternative],
          ...(named ? { unknownField: named } : {}),
        })
      }
      continue
    }

    const rawValue = body.slice(colon + 1)
    // `milestone:` on its own is a keystroke, not a query. Dropping it is
    // what stops the board emptying between the colon and the value.
    if (!rawValue) {
      continue
    }
    const alternatives = splitAlternatives(rawValue)
      .map((part) => readAlternative(part, field.ordered === true))
      .filter((part): part is QueryAlternative => part !== null)
    if (alternatives.length > 0) {
      terms.push({ negate, field, alternatives })
    }
  }
  return terms
}

function matchesAlternative(value: string, alternative: QueryAlternative) {
  const candidate = value.toLowerCase()
  if (alternative.op) {
    // Both sides, or the comparison is a string comparison wearing a date's
    // clothes. `readAlternative` already refuses a half-typed date on the
    // query side; the card side is not validated anywhere — folio passes
    // `created:` through as written — so a card dated `2026-8-1` compared
    // as text sorts after `2026-08-01` and before nothing, and
    // `created:<2026-12-31` quietly drops it. A card whose date is not a
    // date answers no ordered question rather than answering it wrongly.
    if (!FULL_ISO_DATE.test(candidate)) {
      return false
    }
    switch (alternative.op) {
      case ">":
        return candidate > alternative.text
      case ">=":
        return candidate >= alternative.text
      case "<":
        return candidate < alternative.text
      case "<=":
        return candidate <= alternative.text
    }
  }
  return alternative.exact
    ? candidate === alternative.text
    : candidate.includes(alternative.text)
}

function matchesTerm(
  term: QueryTerm,
  card: KanbanCard,
  columnId: string,
  columnTitle: string
) {
  if (!term.field) {
    const haystack =
      `${card.title} ${card.description} ${card.id ?? ""}`.toLowerCase()
    return term.alternatives.some((alternative) =>
      haystack.includes(alternative.text)
    )
  }
  // A card handed in through the `columns` prop, an overlay written by an
  // older build, or a half-formed YAML entry can put a hole where a string
  // belongs; a hole matches nothing rather than crashing the filter.
  const values = term.field
    .values(card, columnId, columnTitle)
    .filter((value): value is string => typeof value === "string")
  const hit = term.alternatives.some((alternative) => {
    // `none` and `any` are the whole is:/has: namespace in two words that
    // work on every field, so the vocabulary stays 100% frontmatter keys.
    // Quoting escapes them: tag:"none" is a tag literally called none.
    if (!alternative.exact && alternative.text === "none") {
      return values.filter(Boolean).length === 0
    }
    if (!alternative.exact && alternative.text === "any") {
      return values.filter(Boolean).length > 0
    }
    return values.some(
      (value) => value && matchesAlternative(value, alternative)
    )
  })
  return term.negate ? !hit : hit
}

function matchesQuery(
  terms: QueryTerm[],
  card: KanbanCard,
  columnId: string,
  columnTitle: string
) {
  return terms.every((term) => matchesTerm(term, card, columnId, columnTitle))
}

function countMatches(board: BoardColumn[], terms: QueryTerm[]) {
  let matched = 0
  for (const column of board) {
    for (const card of column.cards) {
      if (matchesQuery(terms, card, column.id, column.title)) {
        matched++
      }
    }
  }
  return matched
}

/** A value written back into an expression, quoted when it has to be. */
/* The filter, without typing it.

   One panel, and it has to cover the whole language — otherwise it is the
   second store this board deliberately deleted, quietly dropping whatever
   it cannot draw. So: the values that exist on this board, a date
   comparison for `created`, and everything else listed as the raw terms it
   is, removable and never rewritten.

   It holds no state. Every row derives from the parsed expression on the
   way to the screen, so text typed by hand and text written by a click are
   the same text and cannot disagree.

   The counts predict the click. A faceted panel that counts a value as if
   it replaced the current term lies whenever the field already has one —
   clicking ORs into it, so the count has to be of the query you would get,
   not of the value in isolation. */

/* The fields drawn as tri-state checkbox lists: few values, all visible at
   a glance, include and exclude both one press away. */
const CHECK_FIELDS = ["status", "priority", "size"]
/* The one closed vocabulary on the board; the checkboxes list it as a
   scale, not in the order cards happen to mention it. */
const SIZE_ORDER = ["S", "M", "L", "XL"]
/* One value per card: a sole-value picker is their natural shape. The
   board's values with predictive counts, plus "any" to clear — and a
   search box once the value list is long. */
const SELECT_FIELDS = ["type", "milestone", "assignee", "source"]
/* Everything the panel draws; `tag` gets its own input control. */
const PANEL_FIELDS = [...CHECK_FIELDS, ...SELECT_FIELDS, "tag"]

type ValueState = "off" | "in" | "out"

function fieldTerm(terms: QueryTerm[], key: string, negate: boolean) {
  return terms.find(
    (term) =>
      term.field?.key === key &&
      term.negate === negate &&
      !term.alternatives[0]?.op
  )
}

function valueState(
  terms: QueryTerm[],
  key: string,
  value: string
): ValueState {
  const has = (negate: boolean) =>
    fieldTerm(terms, key, negate)?.alternatives.some(
      (alternative) => alternative.text === value.toLowerCase()
    ) ?? false
  if (has(false)) return "in"
  if (has(true)) return "out"
  return "off"
}

/* Rewriting is done by spelling every term back with `termSource`, the same
   function the board uses, so the panel cannot invent a spelling the parser
   would read differently. */
function withValue(
  terms: QueryTerm[],
  key: string,
  value: string,
  next: ValueState
): string {
  const lower = value.toLowerCase()
  const kept: string[] = []
  const alternatives: Record<"in" | "out", string[]> = { in: [], out: [] }

  for (const term of terms) {
    const drawable = term.field?.key === key && !term.alternatives[0]?.op
    if (!drawable) {
      kept.push(termSource(term))
      continue
    }
    const bucket = term.negate ? "out" : "in"
    for (const alternative of term.alternatives) {
      if (alternative.text === lower) continue
      alternatives[bucket].push(
        alternative.exact ? `"${alternative.text}"` : alternative.text
      )
    }
  }
  if (next !== "off") {
    alternatives[next === "in" ? "in" : "out"].push(quoteValue(value))
  }

  const rebuilt = [
    alternatives.in.length ? `${key}:${alternatives.in.join(",")}` : "",
    alternatives.out.length ? `-${key}:${alternatives.out.join(",")}` : "",
  ].filter(Boolean)

  return [...kept, ...rebuilt].join(" ")
}

/* Cards you get with this value on. For a value already on that is the
   current result; for one that is off it is what pressing it would give.
   Always the same question, so the number beside a row never changes
   meaning — the first draft asked "what if you pressed this", which for an
   on value meant counting it *off* and printed 26 beside a checked row. */
function countWith(
  board: BoardColumn[],
  terms: QueryTerm[],
  key: string,
  value: string
) {
  return countMatches(board, parseQuery(withValue(terms, key, value, "in")))
}

/* The one positive value a select can show for this field, "" for none, or
   null when the expression holds something a single-value control cannot
   draw (an OR list, several AND terms) — those terms fall to the "Also"
   chips instead of being lied about. Negated terms are always chips and do
   not affect drawability. */
function soleValue(terms: QueryTerm[], key: string): string | null {
  let found: string | undefined
  for (const term of terms) {
    if (term.field?.key !== key || term.negate || term.alternatives[0]?.op) {
      continue
    }
    if (found !== undefined || term.alternatives.length !== 1) {
      return null
    }
    found = term.alternatives[0].text
  }
  return found ?? ""
}

/* Set the field to exactly one value (or none). Positive non-comparison
   terms of the field are replaced — an explicit choice on the control is
   the reader setting the field, not a silent drop. Negations survive. */
function withSoleValue(
  terms: QueryTerm[],
  key: string,
  value: string | null
): string {
  const kept = terms
    .filter(
      (term) =>
        !(term.field?.key === key && !term.negate && !term.alternatives[0]?.op)
    )
    .map(termSource)
  if (value) {
    kept.push(`${key}:${quoteValue(value)}`)
  }
  return kept.join(" ")
}

function PanelRow({
  label,
  state,
  count,
  onCycle,
}: {
  label: string
  state: ValueState
  count: number
  onCycle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onCycle}
      aria-pressed={state !== "off"}
      className={cn(
        "flex min-h-6 w-full items-center gap-2 rounded-md px-1.5 text-left text-xs transition-colors",
        "hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        state === "off" && "text-muted-foreground",
        state === "in" && "font-medium text-foreground",
        state === "out" &&
          "text-muted-foreground line-through decoration-destructive"
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "flex size-3.5 shrink-0 items-center justify-center rounded-[3px] border",
          state === "in" && "border-primary bg-primary text-primary-foreground",
          state === "out" && "border-destructive text-destructive",
          state === "off" && "border-border"
        )}
      >
        {state === "in" ? <CheckGlyph className="size-2.5" /> : null}
        {state === "out" ? (
          <span className="block h-px w-1.5 bg-destructive" />
        ) : null}
      </span>
      <span className="min-w-0 flex-1 truncate">{label}</span>
      <span className="shrink-0 font-mono text-[11px] text-muted-foreground tabular-nums">
        {count}
      </span>
      <span className="sr-only">
        {state === "in"
          ? " — included, press to exclude"
          : state === "out"
            ? " — excluded, press to clear"
            : " — press to include"}
      </span>
    </button>
  )
}

/* Options that survive the search box: case-blind substring on the label.
   Pure, so the language tests execute it instead of trusting a pin. */
function filterOptions(
  values: [string, string][],
  query: string
): [string, string][] {
  const needle = query.trim().toLowerCase()
  if (!needle) {
    return values
  }
  return values.filter(([, optionLabel]) =>
    optionLabel.toLowerCase().includes(needle)
  )
}

/* A field with few values is a glance; one with many is a search. */
const SEARCH_THRESHOLD = 8

function PanelCombobox({
  label,
  values,
  current,
  countOf,
  onSelect,
}: {
  label: string
  values: [string, string][]
  /** Lowercased sole term value, "" when the field is unset. */
  current: string
  countOf: (value: string) => number
  onSelect: (value: string | null) => void
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const panelRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)
  const listId = `${useId().replace(/:/g, "")}-options`

  const matched = values.find(([value]) => value.toLowerCase() === current)
  const searchable = values.length >= SEARCH_THRESHOLD

  // The same rows the select drew: "any" first, the board's values, and a
  // typed value the board does not have (`milestone:0.9`) still shown
  // rather than silently reading as "any".
  const options: [string, string][] = [
    ["", "any"],
    ...filterOptions(values, search),
  ]
  if (current && !matched) {
    options.push([current, current])
  }
  const activeIndex = Math.min(active, options.length - 1)

  const close = (refocus: boolean) => {
    setOpen(false)
    setSearch("")
    setActive(0)
    if (refocus) {
      triggerRef.current?.focus()
    }
  }
  const openPanel = () => {
    /* The active row opens on the value the field already holds — Enter on
       a just-opened list must keep the filter it found, not clear it to
       "any" at row zero. Unset or unmatched falls back to "any". Search is
       "" here (close resets it), so these are the rows the panel shows. */
    const seeded = options.findIndex(
      ([value]) => value.toLowerCase() === current
    )
    setActive(seeded >= 0 ? seeded : 0)
    setOpen(true)
    /* A mouse open keeps focus wherever it was (the trigger prevents
       mousedown default), and below the search threshold nothing else
       claims it — Escape would then miss this root entirely and fall to
       the rail. Focus the trigger by hand; on a searchable panel the open
       effect hands it on to the search input a frame later. */
    triggerRef.current?.focus()
  }
  const pick = (value: string) => {
    onSelect(value || null)
    close(true)
  }

  // Open: search takes the keyboard when it exists, and the panel walks
  // into view so it never opens under the rail's fold.
  useEffect(() => {
    if (!open) {
      return
    }
    searchRef.current?.focus()
    panelRef.current?.scrollIntoView({ block: "nearest" })
  }, [open])

  // The active row follows the arrows into view.
  useEffect(() => {
    if (open) {
      panelRef.current
        ?.querySelector("[data-active]")
        ?.scrollIntoView({ block: "nearest" })
    }
  }, [open, activeIndex])

  useEffect(() => {
    if (!open) {
      return
    }
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        // `close(false)` inlined: the effect resets state itself rather
        // than closing over a function remade every render.
        setOpen(false)
        setSearch("")
        setActive(0)
      }
    }
    document.addEventListener("mousedown", onPointer)
    return () => document.removeEventListener("mousedown", onPointer)
  }, [open])

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (!open) {
      if (
        event.key === "Enter" ||
        event.key === " " ||
        event.key === "ArrowDown"
      ) {
        event.preventDefault()
        openPanel()
      }
      return
    }
    if (event.key === "Escape") {
      /* Escape belongs to the open panel first. Next hydrates React onto
         `document`, so this handler runs from React's delegated keydown
         listener ON `document` — the same target the rail's dismiss
         listener sits on, and stopPropagation() never suppresses
         same-target listeners. Two belts instead: React's document
         listener was registered at hydration, before the rail's, so
         stopImmediatePropagation() cancels the later one; and the rail
         early-returns on `defaultPrevented`, which preventDefault() sets.
         stopPropagation() stays for non-document embed topologies. */
      event.preventDefault()
      event.stopPropagation()
      event.nativeEvent.stopImmediatePropagation()
      close(true)
      return
    }
    if (event.key === "ArrowDown") {
      event.preventDefault()
      setActive(Math.min(activeIndex + 1, options.length - 1))
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      setActive(Math.max(activeIndex - 1, 0))
    } else if (event.key === "Home" || event.key === "End") {
      /* The textbox owns its caret keys: from the search input Home/End
         move the caret and fall through; from the trigger they jump the
         list's ends. */
      if (event.target === searchRef.current) {
        return
      }
      event.preventDefault()
      setActive(event.key === "Home" ? 0 : options.length - 1)
    } else if (
      event.key === "Enter" ||
      (event.key === " " && event.target !== searchRef.current)
    ) {
      /* Space picks like Enter — the Move-to twin always did, and on the
         trigger button an unhandled Space re-toggled on keyup, silently
         discarding the selection. In the search input a space is a
         character, so the textbox keeps it. First drift caught between
         the two combobox copies; the extraction of their shared cage is
         a carded follow-up. */
      event.preventDefault()
      const option = options[activeIndex]
      if (option) {
        pick(option[0])
      }
    }
  }

  return (
    <div
      ref={rootRef}
      className="relative min-w-0"
      onKeyDown={onKeyDown}
      onBlur={(event) => {
        /* Tab (or the "/" shortcut) can walk focus away with the panel
           still painted, where a stray click meant for the field below
           lands on an option. React's onBlur is delegated `focusout`:
           close, without refocus, when focus settles outside the root —
           a null relatedTarget counts as outside. Mouse picks never get
           here: rows preventDefault on mousedown, so focus never leaves. */
        if (
          open &&
          !rootRef.current?.contains(event.relatedTarget as Node | null)
        ) {
          close(false)
        }
      }}
    >
      <span className="mb-1.5 block px-1.5 font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
        {label}
      </span>
      <button
        type="button"
        ref={triggerRef}
        /* APG select-only combobox: a plain button does not support
           aria-activedescendant, so the trigger carries the combobox role. */
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-activedescendant={open ? `${listId}-${activeIndex}` : undefined}
        aria-label={label}
        /* Safari/macOS Firefox never focus a button on mousedown: with
           focus in the search input the press would blur to body, the
           focusout close would flush before click, and onClick would see
           open===false and reopen. Keep focus put, as the rows do. */
        onMouseDown={(event) => event.preventDefault()}
        onClick={() => (open ? close(true) : openPanel())}
        className="flex h-7 w-full items-center justify-between gap-1 rounded-md border border-border bg-background px-1.5 text-xs text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      >
        <span className="truncate">
          {matched ? matched[0] : current || "any"}
        </span>
        <ChevronDownGlyph className="size-3 shrink-0 text-muted-foreground" />
      </button>
      {open ? (
        <div
          ref={panelRef}
          /* Scrollbar and padding presses must not blur the search input —
             a focusout there would dismiss the panel mid-interaction. The
             input itself keeps its default: caret and selection live there,
             and its mousedown never moves focus out of the root. */
          onMouseDown={(event) => {
            if (event.target !== searchRef.current) {
              event.preventDefault()
            }
          }}
          className="absolute inset-x-0 z-20 mt-1 overflow-hidden rounded-md border border-border bg-card shadow-lg"
        >
          {searchable ? (
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setActive(0)
              }}
              placeholder="search"
              aria-label={`Search ${label.toLowerCase()} values`}
              /* Focus sits here while searching, so the active option is
                 announced from the input, not just the trigger. */
              aria-controls={listId}
              aria-activedescendant={`${listId}-${activeIndex}`}
              className="w-full border-b border-border bg-background px-2 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
          ) : null}
          <ul
            role="listbox"
            id={listId}
            aria-label={label}
            className="m-0 max-h-56 list-none overflow-y-auto p-1"
          >
            {options.map(([value, optionLabel], index) => (
              <li
                key={value || "␀any"}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={
                  value ? value.toLowerCase() === current : current === ""
                }
                data-active={index === activeIndex ? "" : undefined}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => pick(value)}
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-2 rounded-sm px-1.5 py-1 text-xs",
                  index === activeIndex
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground"
                )}
              >
                <span className="truncate">{optionLabel}</span>
                {value ? (
                  <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                    {countOf(value)}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

/* Tags are an open list: an input that suggests the board's tags, and a
   chip per active tag. Adding ORs into the tag term — the same semantics
   the checkbox click had. The draft being typed is input state, not filter
   state: nothing is filtered until it commits. */
function PanelTagInput({
  board,
  terms,
  values,
  onChange,
}: {
  board: BoardColumn[]
  terms: QueryTerm[]
  values: [string, string][]
  onChange: (next: string) => void
}) {
  const [draft, setDraft] = useState("")
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  // Active chips: every positive tag term, whether board-known or not.
  const activeTerms: [string, string][] = []
  for (const term of terms) {
    if (
      term.field?.key === "tag" &&
      !term.negate &&
      !term.alternatives[0]?.op
    ) {
      for (const alternative of term.alternatives) {
        activeTerms.push([alternative.text, alternative.text])
      }
    }
  }
  const activeSet = new Set(activeTerms.map(([value]) => value))
  const suggestions = values.filter(
    ([value]) => !activeSet.has(value.toLowerCase())
  )
  const commit = (raw: string) => {
    const value = raw.trim()
    if (value) {
      onChange(withValue(terms, "tag", value, "in"))
    }
    setDraft("")
    setActiveIndex(0)
  }
  // The same custom dropdown vocabulary the field selects use — a native
  // suggestion list sat here once, and whether it ever appeared was the
  // browser's mood, not the board's behavior.
  const options = filterOptions(suggestions, draft)
  const listOpen = open && options.length > 0
  const listId = "kanban-filter-tag-listbox"
  return (
    <div className="min-w-0">
      <span className="mb-1.5 block px-1.5 font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
        Tag
      </span>
      <div className="relative">
        <input
          type="text"
          value={draft}
          role="combobox"
          aria-expanded={listOpen}
          aria-controls={listId}
          aria-activedescendant={listOpen ? `${listId}-${activeIndex}` : undefined}
          placeholder="add a tag"
          aria-label="Add a tag to the filter"
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onChange={(event) => {
            setDraft(event.target.value)
            setActiveIndex(0)
            setOpen(true)
          }}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown" && listOpen) {
              event.preventDefault()
              setActiveIndex((index) => Math.min(index + 1, options.length - 1))
            } else if (event.key === "ArrowUp" && listOpen) {
              event.preventDefault()
              setActiveIndex((index) => Math.max(index - 1, 0))
            } else if (event.key === "Escape" && listOpen) {
              event.preventDefault()
              setOpen(false)
            } else if (event.key === "Enter") {
              event.preventDefault()
              if (listOpen && options[activeIndex]) {
                commit(options[activeIndex][0])
              } else {
                commit(draft)
              }
            }
          }}
          className="h-7 w-full rounded-md border border-border bg-background px-1.5 text-xs text-foreground placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        />
        {listOpen ? (
          <ul
            role="listbox"
            id={listId}
            aria-label="Tag suggestions"
            className="absolute inset-x-0 z-20 m-0 mt-1 max-h-56 list-none overflow-y-auto rounded-md border border-border bg-card p-1 shadow-lg"
          >
            {options.map(([value, optionLabel], index) => (
              <li
                key={value}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === activeIndex}
                data-active={index === activeIndex ? "" : undefined}
                onMouseEnter={() => setActiveIndex(index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => commit(value)}
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-2 rounded-sm px-1.5 py-1 text-xs",
                  index === activeIndex
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground"
                )}
              >
                <span className="truncate">{optionLabel}</span>
                <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                  {countWith(board, terms, "tag", value)}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      {activeTerms.length > 0 ? (
        <span className="mt-1.5 flex flex-wrap gap-1 px-0.5">
          {activeTerms.map(([value, label]) => (
            <span
              key={value}
              className="inline-flex min-h-6 items-center gap-1 rounded-md border border-border bg-background py-0.5 pr-0.5 pl-1.5 font-mono text-[11px] text-foreground"
            >
              {label}
              <span className="font-mono text-[11px] text-muted-foreground tabular-nums">
                {countWith(board, terms, "tag", value)}
              </span>
              <button
                type="button"
                onClick={() => onChange(withValue(terms, "tag", value, "off"))}
                aria-label={`Remove tag ${label}`}
                className="flex size-5 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                <CloseGlyph className="size-2.5" />
              </button>
            </span>
          ))}
        </span>
      ) : null}
    </div>
  )
}

function FilterPanel({
  id,
  board,
  terms,
  query,
  open,
  workspace,
  railRef,
  onChange,
}: {
  id: string
  board: BoardColumn[]
  terms: QueryTerm[]
  query: string
  open: boolean
  /** On the standalone board page the panel is a flex child of a
   * viewport-height workspace, so on lg it is simply full height with its
   * own scroll — no shell to stretch, nothing to keep sticky. The docs
   * embed keeps the stretched-shell/sticky-inner pair below. */
  workspace: boolean
  railRef: React.RefObject<HTMLDivElement | null>
  onChange: (next: string) => void
}) {
  // Every value this board actually has, per field, in board order. A panel
  // listing fields the board has no values for is a panel about the schema,
  // not about the work.
  const sections = useMemo(
    () =>
      PANEL_FIELDS.map((key) => {
        const field = FIELD_BY_NAME.get(key)
        if (!field) {
          return null
        }
        const seen = new Map<string, string>()
        for (const column of board) {
          if (key === "status") {
            seen.set(column.id, column.title)
            continue
          }
          for (const card of column.cards) {
            for (const value of field.values(card, column.id, column.title)) {
              if (value) {
                seen.set(value, value)
              }
            }
          }
        }
        const values = [...seen.entries()]
        if (key === "size") {
          values.sort(
            (a, b) => SIZE_ORDER.indexOf(a[0]) - SIZE_ORDER.indexOf(b[0])
          )
        }
        return seen.size > 0 ? { key, label: field.label, values } : null
      }).filter((section) => section !== null),
    [board]
  )

  const dateTerm = terms.find(
    (term) => term.field?.key === "created" && term.alternatives[0]?.op
  )

  // A term the panel cannot draw: another field, free text, or a comparison.
  // It is listed as written and never rewritten — dropping it silently is
  // the whole failure this panel exists to avoid. The date control draws
  // dateTerm; a second created comparison (there is no second control) chips.
  const undrawn = terms.filter((term) => {
    if (term === dateTerm) {
      return false
    }
    if (!term.field || Boolean(term.alternatives[0]?.op)) {
      return true
    }
    const key = term.field.key
    if (CHECK_FIELDS.includes(key)) {
      return false
    }
    if (SELECT_FIELDS.includes(key)) {
      return term.negate || soleValue(terms, key) === null
    }
    if (key === "tag") {
      return term.negate
    }
    return true
  })

  const rewriteWithout = (dropped: QueryTerm) => {
    const source = termSource(dropped)
    let done = false
    onChange(
      terms
        .filter((term) => {
          if (!done && termSource(term) === source) {
            done = true
            return false
          }
          return true
        })
        .map(termSource)
        .join(" ")
    )
  }

  const setDate = (op: string, value: string) => {
    const rest = terms.filter((term) => term !== dateTerm).map(termSource)
    onChange(
      [...rest, op && value ? `created:${op}${value}` : ""]
        .filter(Boolean)
        .join(" ")
    )
  }

  // One count per (field, value) per (board, terms) — the checkbox rows
  // recounted the whole board on every unrelated render while the rail
  // sat open (a drag crossing, a combobox hover). A keystroke still pays
  // once per row, because the counts genuinely change; everything else
  // hits the map. Keyed on the terms reference, which the board memoizes
  // per query for exactly this reason.
  const rowCounts: ReadonlyMap<string, number> = useMemo(
    () =>
      new Map(
        sections.flatMap((section) =>
          section.values.map(([value]) => [
            `${section.key}\0${value}`,
            countWith(board, terms, section.key, value),
          ])
        )
      ),
    [board, terms, sections]
  )

  if (!open) {
    return null
  }

  return (
    <div
      id={id}
      ref={railRef}
      data-slot="kanban-filter-panel"
      aria-label="Filter"
      role="group"
      /* A rail beside the board, the full height of the reading. On a
         narrow screen there is no column to give, so the same panel is a
         drawer pinned to the viewport's left edge — in every mode.

         In the docs embed the shell is the surface and the surface runs to
         the board's foot: the grid row is as tall as the board column, and
         with nothing to say otherwise this box stretches to fill it. The
         controls live in the sticky block inside. Sticky dies inside an
         overflow ancestor, so on lg that outer box must never scroll — the
         drawer's max-lg:overflow-y-auto is the one exception, below the
         breakpoint where nothing is sticky.

         In the workspace the section already is the viewport, so none of
         that machinery earns its keep: the panel is a plain flex child
         stretched to the workspace's full height, scrolling its own
         overflow, squared off and ruled from the canvas by its right
         border alone. */
      className={cn(
        "rounded-lg border border-border bg-card",
        "max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-40 max-lg:w-[17rem] max-lg:max-w-[85vw] max-lg:overflow-y-auto max-lg:rounded-none max-lg:border-y-0 max-lg:border-l-0 max-lg:shadow-lg",
        workspace &&
          "lg:w-[17rem] lg:shrink-0 lg:overflow-y-auto lg:rounded-none lg:border-y-0 lg:border-l-0"
      )}
    >
      {/* The block that follows the reader — in the docs embed. It takes
          the padding, sits below the navbar, never exceeds the viewport,
          and scrolls its own overflow, inside a shell that keeps the full
          column height. The workspace panel scrolls itself, so there the
          block only pads. */}
      <div
        className={cn(
          "p-4",
          !workspace &&
            "lg:sticky lg:top-[calc(var(--nextra-navbar-height,0px)+1rem)] lg:max-h-[calc(100vh-var(--nextra-navbar-height,0px)-2rem)] lg:overflow-y-auto"
        )}
      >
        <div className="flex flex-col gap-4">
          {sections.map((section) => {
            if (SELECT_FIELDS.includes(section.key)) {
              return (
                <PanelCombobox
                  key={section.key}
                  label={section.label}
                  values={section.values}
                  current={soleValue(terms, section.key) ?? ""}
                  countOf={(value) =>
                    countMatches(
                      board,
                      parseQuery(withSoleValue(terms, section.key, value))
                    )
                  }
                  onSelect={(value) =>
                    onChange(withSoleValue(terms, section.key, value))
                  }
                />
              )
            }
            if (section.key === "tag") {
              return (
                <PanelTagInput
                  key="tag"
                  board={board}
                  terms={terms}
                  values={section.values}
                  onChange={onChange}
                />
              )
            }
            return (
              <div key={section.key} className="min-w-0">
                <span className="mb-1.5 block px-1.5 font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
                  {section.label}
                </span>
                {section.values.map(([value, label]) => {
                  const state = valueState(terms, section.key, value)
                  return (
                    <PanelRow
                      key={value}
                      label={label}
                      state={state}
                      count={rowCounts.get(`${section.key}\0${value}`) ?? 0}
                      onCycle={() =>
                        onChange(
                          withValue(
                            terms,
                            section.key,
                            value,
                            state === "off"
                              ? "in"
                              : state === "in"
                                ? "out"
                                : "off"
                          )
                        )
                      }
                    />
                  )
                })}
              </div>
            )
          })}

          {/* `created` is the one field with an order, so it gets the one
              control that is not a list. */}
          <div className="min-w-0">
            <span className="mb-1.5 block px-1.5 font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
              Created
            </span>
            <div className="flex items-center gap-1.5 px-1.5">
              <select
                value={dateTerm?.alternatives[0].op ?? ""}
                onChange={(event) =>
                  setDate(
                    event.target.value,
                    dateTerm?.alternatives[0].text ?? ""
                  )
                }
                aria-label="Created comparison"
                className="h-7 rounded-md border border-border bg-background px-1 text-xs text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                <option value="">any</option>
                <option value=">=">on or after</option>
                <option value="<=">on or before</option>
              </select>
              <input
                type="date"
                value={dateTerm?.alternatives[0].text ?? ""}
                onChange={(event) =>
                  setDate(
                    dateTerm?.alternatives[0].op ?? ">=",
                    event.target.value
                  )
                }
                aria-label="Created date"
                className="h-7 min-w-0 flex-1 rounded-md border border-border bg-background px-1.5 font-mono text-xs text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              />
            </div>
          </div>
        </div>

        {undrawn.length > 0 || query ? (
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-border pt-3">
            {undrawn.length > 0 ? (
              <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
                <span className="font-mono text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                  Also
                </span>
                {undrawn.map((term, index) => (
                  <span
                    key={`${termSource(term)}-${index}`}
                    className="inline-flex min-h-6 items-center gap-1 rounded-md border border-border bg-background py-0.5 pr-0.5 pl-1.5 font-mono text-[11px] text-foreground"
                  >
                    {termSource(term)}
                    <button
                      type="button"
                      onClick={() => rewriteWithout(term)}
                      aria-label={`Remove ${termSource(term)}`}
                      className="flex size-5 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      <CloseGlyph className="size-2.5" />
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
            {query ? (
              <button
                type="button"
                onClick={() => onChange("")}
                className="shrink-0 text-xs text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                Clear the filter
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

/* Why the board is empty, in the terms that emptied it.

   Three different mistakes used to produce the same four lines of "No cards
   match the filters.": a field name typed wrong (`tagg:spec`, which falls
   back to a text search and finds nothing), a real field with a value no
   card has (`priority:nope`), and an ordinary text search that misses. The
   board said the same thing to all three and named none of them, so the
   only way forward was to delete characters until cards came back.

   Each term is re-run on its own. A term that matches nothing by itself is
   the one that emptied the board, and there may be more than one. A term
   that matches on its own is not mentioned: it did its job, and the
   combination is what failed. */
function FilterDiagnosis({
  board,
  terms,
}: {
  board: BoardColumn[]
  terms: QueryTerm[]
}) {
  const barren = terms.filter((term) => countMatches(board, [term]) === 0)
  // Nothing to add: every term matches something and only together do they
  // match nothing. Saying "some combination of these" helps no one.
  const reasons = barren.length > 0 ? barren : []

  return (
    <div className="mt-1 max-w-[60ch]">
      <p className="m-0 text-sm text-foreground">
        Nothing matches this filter.
      </p>
      {reasons.length > 0 ? (
        <ul className="m-0 mt-2 list-none space-y-1 p-0">
          {reasons.map((term) => (
            <li
              key={termSource(term)}
              className="text-xs text-muted-foreground"
            >
              <code className="font-mono text-foreground">
                {termSource(term)}
              </code>{" "}
              matches no card
              {term.unknownField ? (
                <>
                  {" — "}
                  <code className="font-mono">{term.unknownField}</code> is not
                  a field, so it was searched as text
                </>
              ) : null}
              .
            </li>
          ))}
        </ul>
      ) : (
        <p className="m-0 mt-2 text-xs text-muted-foreground">
          Each term matches something on its own; together they match nothing.
        </p>
      )}
    </div>
  )
}

/* A term, spelled the way it was typed. The board has to be able to name
   the term that emptied it, and the parsed shape is not something anyone
   typed. */
function termSource(term: QueryTerm) {
  const value = term.alternatives
    .map((alternative) => {
      const text = alternative.exact
        ? `"${alternative.text}"`
        : alternative.text
      return `${alternative.op ?? ""}${text}`
    })
    .join(",")
  if (!term.field) {
    return value
  }
  return `${term.negate ? "-" : ""}${term.field.key}:${value}`
}

function quoteValue(value: string) {
  return /[\s,"]/.test(value) ? `"${value.replace(/"/g, "")}"` : value
}

/* ------------------------------------------------------------------ */
/* Pieces                                                               */
/*                                                                      */
/* Type scale. Three declared sizes, each a named Tailwind step so it   */
/* carries its own line-height. An arbitrary `text-[Npx]` sets the font */
/* size only and inherits a 1.5 ratio from wherever it lands, which is  */
/* how this file ended up with seven sizes and accidental leading.      */
/*                                                                      */
/*   S4  text-lg  18px  the card dialog's own title. One use, off-board */
/*   S3  text-sm  14px  sentences: the board h1, the dialog description,*/
/*                      the linked-page line, the no-columns message    */
/*   S2  text-xs  12px  everything scanned or clicked: card titles,     */
/*                      controls, counts, values, criteria, trail,      */
/*                      chips, placeholders                             */
/*                                                                      */
/* S2 carries two registers rather than a fourth size. Structure labels */
/* (column names, field names, the artifact kind, the blocked badge)    */
/* are `font-mono text-xs tracking-[0.08em] uppercase                   */
/* text-muted-foreground`. At 12px their cap height is 8.8px against    */
/* the 6.4px x-height of 12px sentence-case body, so they read larger   */
/* without being larger. Values the board did not author (tag names,    */
/* milestones, ids) stay in the case they were written in. Chrome that  */
/* stands in for absent content — "No cards in this column", "+3 more"  */
/* — takes S2 as well, even though it is a sentence: it is a state, not */
/* something to read.                                                   */
/*                                                                      */
/* Chips are `px-1 leading-4` with no vertical padding: the 16px line   */
/* box is the chip. 12px is the floor. Six labels used to sit at 9px,   */
/* uppercase and tracked, which is where 9px hurts most.                */
/* ------------------------------------------------------------------ */

/* The count reads in the column header's own register — mono, 11px,
   tracked — so `BACKLOG … 22` is one typographic line. It used to be a
   6px-tall chip on limited columns and bare text on the rest, which made
   the four headers sit at four different heights: the row that should be
   the board's steadiest line was its raggedest. Over the limit changes the
   colour, which is the whole signal; a box around it was never the news. */
const COUNT_REGISTER = "font-mono text-[11px] leading-4 tracking-[0.14em]"

function WipBadge({ count, limit }: { count: number; limit: number | null }) {
  if (limit === null) {
    return (
      <span className={cn(COUNT_REGISTER, "text-muted-foreground")}>
        {count}
      </span>
    )
  }

  const over = count > limit

  return (
    <span
      data-over-limit={over ? "" : undefined}
      className={cn(
        COUNT_REGISTER,
        over ? "font-semibold text-warning" : "text-muted-foreground"
      )}
    >
      {count}/{limit}
      {/* The state is in the colour and in this line. It used to also be a
          `title`, which is mouse-only — it never reaches a keyboard or a
          touch screen — so it was a third copy of a fact already said
          twice, and one that only some readers could get at. */}
      <span className="sr-only">
        {over ? " cards, over the limit" : " cards, within the limit"}
      </span>
    </span>
  )
}

/* The milestone, as a reading. Not a link.

   It used to navigate to the roadmap step it names, and it sits on the
   card's first line, directly above the title — so the top of a card was a
   link away from the board and the rest of it opened the card. Two
   destinations in one object, and the one you hit by aiming slightly high
   took you off the page.

   The card has one job on the board: open. The roadmap link lives in the
   dialog's rail, one press further in, where nothing else is competing for
   the same pixels. */
function CardKey({ card }: { card: KanbanCard }) {
  const parts = [
    card.type,
    card.phaseTitle ? `${card.phaseTitle} · ${card.milestone}` : card.milestone,
  ].filter(Boolean)
  if (parts.length === 0) {
    return null
  }
  return (
    <span className="block font-mono text-[11px] leading-4 tracking-[0.14em] text-primary uppercase">
      {parts.join(" · ")}
    </span>
  )
}

function CardTitle({ card }: { card: KanbanCard }) {
  // One step for every card title. The non-compact branch was unreachable
  // (full boards render their title as the dialog trigger button), and the
  // named step brings its own 16px line box, so card height stops
  // depending on the leading the card happens to inherit.
  const sizing = "text-xs font-semibold"
  if (card.link) {
    return (
      <a
        href={card.link}
        className={cn(
          "text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground",
          sizing
        )}
      >
        {card.title}
      </a>
    )
  }
  return <p className={cn("m-0 text-foreground", sizing)}>{card.title}</p>
}

function CheckGlyph({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={3}
      className={className}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  )
}

/* One pen for the whole board. Every control mark below is drawn on the
   same 16-unit grid at stroke 1.5 as CheckGlyph, so a chevron in a move
   button and a column mark in a header carry identical ink at identical
   rendered sizes. The unicode characters these replace never did: a glyph
   renders at whatever weight the body font gives it, and it shifts
   between platforms. */
function Glyph({ d, className }: { d: string; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("shrink-0", className)}
    >
      <path d={d} />
    </svg>
  )
}

/* Drawn symmetric about (8, 8), so any control centres it by geometry alone
   and no optical inset is needed. */
function ChevronDownGlyph({ className }: { className?: string }) {
  return <Glyph className={className} d="m4 6 4 4 4-4" />
}

/* Three rules, narrowing. The field used to open with a magnifying glass,
   which promises search — type a word, get matches. This one is a filter
   language: the word is the fallback, not the point. */
function FilterGlyph({ className }: { className?: string }) {
  return <Glyph className={className} d="M2.5 4h11M4.5 8h7M6.5 12h3" />
}

function CloseGlyph({ className }: { className?: string }) {
  return <Glyph className={className} d="M12 4 4 12M4 4l8 8" />
}

/* A card is a file on disk, so the dialog opens with the mark for one. */
function FileGlyph({ className }: { className?: string }) {
  return (
    <Glyph
      className={className}
      d="M9 2H4.5v12h7V4.5M9 2l2.5 2.5M9 2v2.5h2.5"
    />
  )
}

function PaperclipGlyph({ className }: { className?: string }) {
  return (
    <Glyph
      className={className}
      d="m14.3 7.4-6.1 6.1a4 4 0 0 1-5.7-5.7l5.7-5.7a2.7 2.7 0 0 1 3.8 3.8L6.3 11.6a1.3 1.3 0 0 1-1.9-1.9l5.7-5.6"
    />
  )
}

function ClockGlyph({ className }: { className?: string }) {
  return (
    <Glyph
      className={className}
      d="M8 1.75a6.25 6.25 0 1 0 0 12.5A6.25 6.25 0 0 0 8 1.75ZM8 4.5V8l2.5 1.5"
    />
  )
}

function BubbleGlyph({ className }: { className?: string }) {
  return (
    <Glyph
      className={className}
      d="M14 10a1.33 1.33 0 0 1-1.33 1.33H4.67L2 14V3.33A1.33 1.33 0 0 1 3.33 2h9.34A1.33 1.33 0 0 1 14 3.33z"
    />
  )
}

/* One mark per artifact kind, on the same 16-unit pen as every other
   glyph. Unknown kinds fall back to the plain file. */
const ARTIFACT_GLYPH_D: Record<string, string> = {
  doc: "M9 2H4.5v12h7V4.5M9 2l2.5 2.5M9 2v2.5h2.5M6.5 9.5h3M6.5 12h3",
  api: "M6.5 2.5C5 2.5 5.25 4 5.25 5.5S3.5 8 3.5 8s1.75 1 1.75 2.5S5 13.5 6.5 13.5M9.5 2.5c1.5 0 1.25 1.5 1.25 3S12.5 8 12.5 8s-1.75 1-1.75 2.5.25 3-1.25 3",
  file: "M9 2H4.5v12h7V4.5M9 2l2.5 2.5M9 2v2.5h2.5",
  pr: "M6.25 3.5a1.75 1.75 0 1 1-3.5 0 1.75 1.75 0 0 1 3.5 0ZM4.5 5.25v5.5M6.25 12.5a1.75 1.75 0 1 1-3.5 0 1.75 1.75 0 0 1 3.5 0Zm7 0a1.75 1.75 0 1 1-3.5 0 1.75 1.75 0 0 1 3.5 0ZM8.5 3.5H10a1.5 1.5 0 0 1 1.5 1.5v5.75",
  url: "M8 1.75a6.25 6.25 0 1 0 0 12.5A6.25 6.25 0 0 0 8 1.75ZM1.75 8h12.5M8 1.75C10 3.75 10 12.25 8 14.25 6 12.25 6 3.75 8 1.75Z",
}

/* One hue per kind, from the theme's own chart family, so five kinds
   read apart at a glance without inventing a palette. `file` keeps the
   board's ink: it is the unmarked case, and a band where every tile is
   tinted says nothing. */
const ARTIFACT_KIND_TINT: Record<string, string> = {
  doc: "border-chart-5/35 bg-chart-5/10 text-chart-5",
  api: "border-warning/35 bg-warning/10 text-warning",
  pr: "border-chart-3/45 bg-chart-3/10 text-chart-3",
  url: "border-chart-4/35 bg-chart-4/10 text-chart-4",
}

/* A card's own files are published by the build under /_folio/kanban/<id>/,
   and a project site can sit under a base path, so a site-absolute artifact
   href needs the same prefix every other emitted link in this template gets.
   A `url:` artifact was authored as a URL and is left exactly as written. */
const FOLIO_BASE_PATH =
  process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""

function artifactHref(href: string): string {
  if (!href.startsWith("/") || href.startsWith("//")) return href
  if (!FOLIO_BASE_PATH || FOLIO_BASE_PATH === "/") return href
  return `${FOLIO_BASE_PATH}${href}`
}

/* A mail's attachment, not a rail chip. The kind is a tinted icon square
   with the label beside it and the target as written under that in mono.
   Still no `title`: a clipped path behind a tooltip is mouse-only, and
   everything the tile knows is drawn where every reader can finish it.
   A tile with `onOpen` reads in the drawer instead of leaving the board;
   the rest keep the band's old manners — a link when the build resolved
   one, a plain path when it did not. */
function ArtifactTile({
  artifact,
  current = false,
  onOpen,
}: {
  artifact: KanbanArtifact
  /** Whether this tile's artifact is the one open in the drawer. */
  current?: boolean
  onOpen?: (opener: HTMLElement) => void
}) {
  // PR targets are numbers, not paths; everything else falls back to the
  // target's basename when no label was authored.
  const fallback =
    artifact.kind === "pr"
      ? `#${artifact.target}`
      : artifact.target.split("/").pop() || artifact.target
  const label = artifact.label || fallback
  // The mono line adds the where, as the author wrote it: a derived
  // sibling's display is its bare name, because the card's own directory
  // is the one place a target never needs to say where it is. When the
  // line would only repeat the label — a bare URL, an unlabelled PR whose
  // label already is the number — the `detail !== label` guard below
  // keeps it home; a labelled PR keeps its number, because "Ship the
  // parser" alone names no PR.
  const detail =
    artifact.kind === "pr"
      ? `#${artifact.target}`
      : artifact.display || artifact.target
  const body = (
    <>
      <span
        aria-hidden="true"
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded-md border",
          ARTIFACT_KIND_TINT[artifact.kind] ??
            "border-border bg-muted/40 text-muted-foreground"
        )}
      >
        <Glyph
          className="size-4"
          d={ARTIFACT_GLYPH_D[artifact.kind] ?? ARTIFACT_GLYPH_D.file}
        />
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="text-xs leading-4 font-medium text-foreground">
          <span className="sr-only">{`${artifact.kind}: `}</span>
          {label}
        </span>
        {detail && detail !== label ? (
          <span className="font-mono text-[11px] leading-4 break-all text-muted-foreground">
            {detail}
          </span>
        ) : null}
      </span>
    </>
  )
  const base =
    "inline-flex min-w-0 items-center gap-2.5 rounded-md border border-border bg-background py-1.5 pr-3 pl-1.5"
  if (onOpen) {
    return (
      <button
        type="button"
        aria-current={current ? "true" : undefined}
        onClick={(event) => onOpen(event.currentTarget)}
        className={cn(
          base,
          "cursor-pointer text-left transition-colors hover:border-foreground/40 hover:bg-muted/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
          current && "border-foreground/50 bg-muted/40"
        )}
      >
        {body}
      </button>
    )
  }
  if (artifact.href) {
    return (
      <a
        href={artifactHref(artifact.href)}
        target="_blank"
        rel="noreferrer"
        className={cn(
          base,
          "transition-colors hover:border-foreground/40 hover:bg-muted/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        )}
      >
        {body}
      </a>
    )
  }
  return <span className={base}>{body}</span>
}

/* Which surface a `doc:` or `file:` artifact opens on. The build resolved
   an owned target to one of two places: a compiled docs page (`page`), or
   the raw published file under /_folio/kanban/<id>/ (`asset`). `pr:` and
   `url:` artifacts were authored as addresses somewhere else and keep the
   band's link out; an empty href stays the plain path it always was. */
type ReaderMode = "page" | "asset"

function readerMode(artifact: KanbanArtifact): ReaderMode | null {
  if (artifact.kind !== "doc" && artifact.kind !== "file") {
    return null
  }
  if (!artifact.href) {
    return null
  }
  return artifact.href.startsWith("/_folio/") ? "asset" : "page"
}

/* The reader: a drawer from the board's left edge, so an artifact reads
   without leaving the kanban. A `page` artifact is the docs page the build
   already compiled — fetched and unwrapped to its article body, which
   arrives styled because both pages share one stylesheet bundle; rendering
   markdown here instead would be a second pipeline to keep honest. An
   `asset` artifact is the raw published file in a sandboxed frame:
   prototypes stay live and their scripts never reach the board. Prototypes
   were built for a full window and open wide; documents open at a reading
   measure; the header trades the two. */
function ArtifactReader({
  artifact,
  wide,
  onToggleWide,
  onClose,
}: {
  artifact: KanbanArtifact
  wide: boolean
  onToggleWide: () => void
  onClose: () => void
}) {
  const mode = readerMode(artifact)
  const label =
    artifact.label || artifact.target.split("/").pop() || artifact.target
  const closeRef = useRef<HTMLButtonElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  // Keyed by target, so switching artifacts drops the old page instead of
  // showing it under the new header while the fetch runs. `html: null` is
  // the fetch's own verdict that the target has no readable page.
  const [result, setResult] = useState<{
    target: string
    html: string | null
  } | null>(null)

  useEffect(() => {
    if (mode !== "page") {
      return
    }
    const target = artifact.target
    let cancelled = false
    const load = async () => {
      try {
        const response = await fetch(artifactHref(artifact.href))
        if (!response.ok) {
          throw new Error(String(response.status))
        }
        const parsed = new DOMParser().parseFromString(
          await response.text(),
          "text/html"
        )
        // The article body every compiled page in this template carries.
        // Nothing found means the target is not a page this site published.
        const article =
          parsed.querySelector("main[data-pagefind-body]") ??
          parsed.querySelector("article")
        if (!article) {
          throw new Error("no article")
        }
        if (!cancelled) {
          setResult({ target, html: article.innerHTML })
        }
      } catch {
        if (!cancelled) {
          setResult({ target, html: null })
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [mode, artifact.href, artifact.target])

  const page = result && result.target === artifact.target ? result : null
  const loaded = page !== null && page.html !== null
  const failed = page !== null && page.html === null

  // Focus moves into the drawer: onto the document scroller when there is
  // one (arrow keys read immediately), onto the close button for a frame —
  // focus inside a sandboxed iframe takes Escape with it.
  useEffect(() => {
    if (mode === "page") {
      scrollRef.current?.focus()
    } else {
      closeRef.current?.focus()
    }
  }, [mode, artifact.target])

  // The page body is injected here, not through React: it is the site's
  // own compiled output — the same markup the band's link out opens — and
  // the effect assignment is the pipeline the reading-rail prototype
  // proved. Script elements parsed this way stay inert.
  //
  // The injected page keeps its heading anchors. A `#hash` link resolves in
  // this document — the browser writes the hash and scrolls the drawer, no
  // reload — and hashchange re-applies it, so a pasted heading link lands
  // even though the fetch finishes after the load. Every other link leaves
  // for its own tab; the board stays.
  useEffect(() => {
    const container = contentRef.current
    if (!container || !page || page.html === null) {
      return
    }
    container.innerHTML = page.html
    // Injected markup never hydrates, so any control that survived the
    // copy — the page's Ask AI trigger, the code-copy buttons — would draw
    // and do nothing. A control that cannot do what it draws is worse
    // than none.
    for (const button of Array.from(container.querySelectorAll("button"))) {
      button.remove()
    }
    for (const anchor of Array.from(
      container.querySelectorAll<HTMLAnchorElement>("a[href]")
    )) {
      const href = anchor.getAttribute("href") ?? ""
      if (href.startsWith("#")) {
        continue
      }
      anchor.setAttribute("target", "_blank")
      anchor.setAttribute("rel", "noreferrer")
    }
    const applyHash = () => {
      const raw = window.location.hash.slice(1)
      if (!raw) {
        return
      }
      let id = raw
      try {
        id = decodeURIComponent(raw)
      } catch {
        // A malformed escape names no heading.
      }
      container
        .querySelector(`#${CSS.escape(id)}`)
        ?.scrollIntoView({ block: "start" })
    }
    applyHash()
    window.addEventListener("hashchange", applyHash)
    return () => window.removeEventListener("hashchange", applyHash)
  }, [page])

  return (
    <aside
      data-slot="kanban-artifact-drawer"
      aria-label={`Reading ${label}`}
      className={cn(
        "absolute inset-y-0 left-0 flex flex-col border-r border-border bg-card shadow-2xl",
        "animate-in duration-200 slide-in-from-left-[100%] motion-reduce:animate-none",
        "transition-[width] motion-reduce:transition-none",
        wide ? "w-[min(96vw,90rem)]" : "w-[min(94vw,46rem)]"
      )}
    >
      <header className="flex shrink-0 items-center gap-3 border-b border-border px-5 py-3">
        <span
          aria-hidden="true"
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-md border",
            ARTIFACT_KIND_TINT[artifact.kind] ??
              "border-border bg-muted/40 text-muted-foreground"
          )}
        >
          <Glyph
            className="size-4"
            d={ARTIFACT_GLYPH_D[artifact.kind] ?? ARTIFACT_GLYPH_D.file}
          />
        </span>
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate text-sm leading-5 font-medium text-foreground">
            {label}
          </span>
          <span className="truncate font-mono text-[11px] leading-4 text-muted-foreground">
            {artifact.target}
          </span>
        </span>
        {/* A long document eventually wants a full window with a stable
            address, and that address already exists; the drawer never
            replaces it. */}
        <a
          href={artifactHref(artifact.href)}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-sm text-xs text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          Open full
        </a>
        <button
          type="button"
          onClick={onToggleWide}
          aria-pressed={wide}
          className={cn(
            "flex h-7 shrink-0 items-center rounded-md border border-border px-2 text-xs transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
            wide
              ? "bg-muted text-foreground"
              : "bg-background text-muted-foreground"
          )}
        >
          Full width
        </button>
        <kbd className="flex h-7 items-center rounded border border-border bg-background px-1.5 font-mono text-xs text-muted-foreground">
          Esc
        </kbd>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label="Close reader"
          className="flex size-7 shrink-0 items-center justify-center rounded-md border border-border bg-background text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <CloseGlyph className="size-3.5" />
        </button>
      </header>
      {mode === "asset" ? (
        <iframe
          sandbox="allow-scripts"
          src={artifactHref(artifact.href)}
          title={label}
          className="min-h-0 w-full flex-1 border-0 bg-background"
        />
      ) : (
        <div
          ref={scrollRef}
          tabIndex={0}
          role="group"
          aria-label="Document"
          className="min-h-0 flex-1 overflow-y-auto focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
        >
          {loaded ? (
            <div
              ref={contentRef}
              /* The effect above fills this in. The classes are the
                 compiled page's own text colors, so the injected body
                 reads in both themes exactly as it does under /docs. */
              className="x:text-slate-700 x:dark:text-slate-200 mx-auto w-full max-w-[76ch] min-w-0 px-8 py-6 break-words"
            />
          ) : failed ? (
            // The closed door: the target is a path, printed as one —
            // never a dead link.
            <div className="mx-auto w-full max-w-[76ch] px-8 py-6">
              <p className="m-0 text-sm text-muted-foreground">
                This target has no published page the board can read.
              </p>
              <p className="m-0 mt-2 font-mono text-xs break-all text-foreground">
                {artifact.target}
              </p>
            </div>
          ) : (
            <p className="m-0 px-8 py-6 font-mono text-xs text-muted-foreground">
              Loading…
            </p>
          )}
        </div>
      )}
    </aside>
  )
}

/* The five rules. `mark` is the character the rule is about, highlighted in
   the example so the eye finds the rule rather than reading the sentence
   beside it — a syntax reference is scanned, not read. */
const SYNTAX_RULES: { example: string; mark: string; meaning: string }[] = [
  {
    example: "tag:spec priority:high",
    mark: " ",
    meaning: "and — every term must match",
  },
  { example: "tag:spec,launch", mark: ",", meaning: "or — either value" },
  { example: "-tag:spec", mark: "-", meaning: "not — exclude these" },
  {
    example: 'tag:"core"',
    mark: '"',
    meaning: "exact — the whole value, not part of it",
  },
  {
    example: "milestone:none",
    mark: "none",
    // Spelled as a whole token rather than as `any` in backticks: this is
    // one string, read aloud by the field's description and printed by the
    // panel, and neither renders Markdown.
    meaning: "unset — milestone:any asks the opposite",
  },
]

/* The same five rules, always in the DOM, for the field's
   `aria-describedby`. The visible copy appears only while the field has
   focus, and a description that does not exist until you focus something
   is a description nobody is ever read. Costs a screen reader user one
   sentence; costs everyone else nothing. */
function SyntaxRules({ id }: { id: string }) {
  return (
    <span id={id} className="sr-only">
      Filter expression.{" "}
      {SYNTAX_RULES.map((rule) => `${rule.example} — ${rule.meaning}`).join(
        ". "
      )}
      .{" Fields: "}
      {FILTER_FIELDS.map((field) => field.key).join(", ")}. Anything else is
      searched as text.
    </span>
  )
}

/* ------------------------------------------------------------------ */
/* Card prose                                                           */
/* ------------------------------------------------------------------ */

/* Cards are markdown files, and the dialog is where they talk — so it
   renders the subset the board's own cards actually write: inline code,
   bold, http(s) links, and `./` links to the card's own siblings. One
   left-to-right pass, so a mark inside a code span stays literal; an
   unmatched mark stays prose (a stray asterisk is text, not a crash);
   a link whose target is neither http(s) nor `./` never becomes a
   token at all — the scheme guard is the grammar, not a sanitizer, and
   `./` is the one relative form it admits because resolveCardLink below
   decides what, if anything, that form may reach. Pure and extracted
   into the node harness like the filter language. */
type MdToken =
  | { kind: "text"; text: string }
  | { kind: "code"; text: string }
  | { kind: "bold"; text: string }
  | { kind: "link"; text: string; href: string }

const INLINE_MD =
  /``((?:[^`]|`(?!`))+)``|`([^`]+)`|\*\*([^*]+)\*\*|\[([^\]]+)\]\(((?:https?:\/\/|\.\/)[^)\s]+)\)/g

function parseInlineMd(text: string): MdToken[] {
  const tokens: MdToken[] = []
  let last = 0
  for (const match of text.matchAll(INLINE_MD)) {
    const index = match.index ?? 0
    if (index > last) {
      tokens.push({ kind: "text", text: text.slice(last, index) })
    }
    if (match[1] !== undefined) {
      // CommonMark double-backtick span — how a card quotes a backtick,
      // and how this very feature's spec card writes `` `code` ``. Left
      // out at first, the two delimiters re-tokenized as stray single
      // spans and the "literal" examples between them went live. One
      // space of padding strips when both sides carry it, per spec.
      const inner = match[1]
      const padded =
        inner.startsWith(" ") && inner.endsWith(" ") && inner.trim() !== ""
      tokens.push({ kind: "code", text: padded ? inner.slice(1, -1) : inner })
    } else if (match[2] !== undefined) {
      tokens.push({ kind: "code", text: match[2] })
    } else if (match[3] !== undefined) {
      tokens.push({ kind: "bold", text: match[3] })
    } else {
      tokens.push({ kind: "link", text: match[4], href: match[5] })
    }
    last = index + match[0].length
  }
  if (last < text.length) {
    tokens.push({ kind: "text", text: text.slice(last) })
  }
  return tokens
}

/* Where a `./` link in a card's prose lands. The spec sentence on the
   epic card is "references are relative, and identical everywhere": the
   string that opens a sibling in an editor opens it here. The written
   target matches the card's own artifacts first — by display (the bare
   derived name or the exact written form) or by target (the resolved
   path under the card's directory) — and borrows that artifact's
   build-resolved href; an artifact the build left unlinked stays
   unlinked here too. Anything unmatched falls back to the raw bundle at
   /_folio/kanban/<id>/, which publishes the card's directory whole. A
   path that climbs out (`..`, a `.` hop, an empty segment) resolves to
   nothing, and nothing renders as the literal text it was — the same
   answer every non-link string already gets. Pure, like the grammar it
   extends, and executed by the test suite under node. */
type CardLinkResolution =
  | { kind: "artifact"; index: number }
  | { kind: "raw"; href: string }

function resolveCardLink(
  target: string,
  cardId: string,
  artifacts: KanbanArtifact[]
): CardLinkResolution | null {
  if (!target.startsWith("./")) {
    return null
  }
  const path = target.slice(2)
  const index = artifacts.findIndex(
    (artifact) =>
      artifact.display === target ||
      artifact.display === path ||
      artifact.target === path ||
      (cardId !== "" && artifact.target.endsWith(`/${cardId}/${path}`))
  )
  if (index >= 0) {
    return artifacts[index].href ? { kind: "artifact", index } : null
  }
  if (cardId === "") {
    return null
  }
  const segments = path.split("/")
  if (
    segments.some(
      (segment) => segment === "" || segment === "." || segment === ".."
    )
  ) {
    return null
  }
  return { kind: "raw", href: `/_folio/kanban/${cardId}/${path}` }
}

/* The prose grammar one level above the spans: a card description is
   blocks. Blank lines split paragraphs, consecutive `- ` lines are a
   list (numbered lines an ordered one, with no blank line required
   after a lead-in sentence), and a dash inside a sentence stays prose.
   Pure and executed by the test suite, like parseInlineMd below. */
type MdBlock =
  | { kind: "paragraph"; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }

function parseMdBlocks(text: string): MdBlock[] {
  const blocks: MdBlock[] = []
  // Cards are repository files; one written on Windows carries \r\n, which
  // would defeat the blank-line split and leave \r inside list items.
  for (const chunk of text.replace(/\r\n/g, "\n").split(/\n{2,}/)) {
    let paragraph: string[] = []
    let list: { ordered: boolean; items: string[] } | null = null
    const flushParagraph = () => {
      if (paragraph.length) {
        blocks.push({ kind: "paragraph", text: paragraph.join("\n") })
        paragraph = []
      }
    }
    const flushList = () => {
      if (list) {
        blocks.push({ kind: "list", ordered: list.ordered, items: list.items })
        list = null
      }
    }
    for (const line of chunk.split("\n")) {
      const bullet = /^\s*- +(.*)$/.exec(line)
      const numbered = bullet ? null : /^\s*\d+[.)] +(.*)$/.exec(line)
      if (bullet || numbered) {
        flushParagraph()
        const ordered = numbered !== null
        if (!list || list.ordered !== ordered) {
          flushList()
          list = { ordered, items: [] }
        }
        list.items.push((bullet ?? numbered)![1])
      } else if (line.trim()) {
        flushList()
        paragraph.push(line)
      }
    }
    flushParagraph()
    flushList()
  }
  return blocks
}

/* The card whose prose is being rendered: what its `./` links resolve
   against, and the drawer a readable one opens in — onOpen is the
   dialog's openReader, the same path a band tile's click takes. Only
   the description passes it; a criterion, a trail note or a comment
   keeps the literal text, exactly as before. */
interface CardLinkContext {
  cardId: string
  artifacts: KanbanArtifact[]
  onOpen: (index: number, opener: HTMLElement) => void
}

/* Tokens to React nodes — never markup handed to the DOM as a string.
   This file has no dangerous innerHTML anywhere, and this component is
   why it never needs any. */
function MdInline({ text, links }: { text: string; links?: CardLinkContext }) {
  return (
    <>
      {parseInlineMd(text).map((token, index) => {
        if (token.kind === "code") {
          return (
            <code
              key={index}
              className="rounded bg-muted/60 px-1 font-mono text-[0.85em] text-foreground"
            >
              {token.text}
            </code>
          )
        }
        if (token.kind === "bold") {
          return (
            <strong key={index} className="font-semibold text-foreground">
              {token.text}
            </strong>
          )
        }
        if (token.kind === "link") {
          if (token.href.startsWith("./")) {
            const resolved = links
              ? resolveCardLink(token.href, links.cardId, links.artifacts)
              : null
            if (!links || !resolved) {
              // No card to resolve against, or a target that resolves to
              // nothing: the literal markdown is the safe rendering.
              return (
                <Fragment key={index}>{`[${token.text}](${token.href})`}</Fragment>
              )
            }
            if (resolved.kind === "artifact") {
              const artifact = links.artifacts[resolved.index]
              if (readerMode(artifact)) {
                return (
                  <button
                    key={index}
                    type="button"
                    onClick={(event) =>
                      links.onOpen(resolved.index, event.currentTarget)
                    }
                    className="cursor-pointer rounded-sm text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                  >
                    {token.text}
                  </button>
                )
              }
            }
            return (
              <a
                key={index}
                href={artifactHref(
                  resolved.kind === "artifact"
                    ? links.artifacts[resolved.index].href
                    : resolved.href
                )}
                target="_blank"
                rel="noreferrer"
                className="rounded-sm text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                {token.text}
              </a>
            )
          }
          return (
            <a
              key={index}
              href={token.href}
              target="_blank"
              rel="noreferrer"
              className="rounded-sm text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              {token.text}
            </a>
          )
        }
        return <Fragment key={index}>{token.text}</Fragment>
      })}
    </>
  )
}

function CriteriaList({ criteria }: { criteria: KanbanCriterion[] }) {
  const done = criteria.filter((criterion) => criterion.done).length
  return (
    <div>
      {/* No border-b here: the progress track under the label is already a
          full-width border-coloured line, and at 0 done the two drew as a
          double rule. The bar is the section's separator. */}
      <div className="mb-2">
        <div className="flex items-baseline justify-between">
          <p className="m-0 flex items-center gap-1.5 font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
            <CheckGlyph className="size-3" />
            Acceptance criteria
          </p>
          <p
            className={cn(
              "m-0 font-mono text-xs tabular-nums",
              done === criteria.length
                ? "text-primary"
                : "text-muted-foreground"
            )}
          >
            {done} / {criteria.length}
          </p>
        </div>
        {/* How far along, at a glance. "3 / 7" is a fact you have to read
            and then divide; the bar is the same fact already divided, and
            it is the one thing on this card that changes as work happens. */}
        <div
          aria-hidden="true"
          className="mt-1.5 h-0.5 w-full overflow-hidden rounded-full bg-border"
        >
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${(done / criteria.length) * 100}%` }}
          />
        </div>
      </div>
      <ul className="m-0 grid list-none gap-1.5 p-0">
        {criteria.map((criterion, index) => (
          <li
            key={`${criterion.text}-${index}`}
            className="flex items-start gap-2"
          >
            {/* State, not a control. The card file on disk is the source of
                truth and the browser never writes it, so a disabled
                checkbox was offering an input nobody was allowed to use.
                A drawn box says the same thing without the offer, and the
                strikethrough goes with it: a closed card ran six struck
                lines, which is the least readable way to say "done". */}
            <span
              aria-hidden="true"
              className={cn(
                "mt-0.5 flex size-3.5 shrink-0 items-center justify-center rounded-[3px] border",
                criterion.done
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border"
              )}
            >
              {criterion.done ? <CheckGlyph className="size-2.5" /> : null}
            </span>
            <span
              className={cn(
                "text-xs leading-5 break-words",
                criterion.done ? "text-muted-foreground" : "text-foreground"
              )}
            >
              <span className="sr-only">
                {criterion.done ? "Done: " : "Not done: "}
              </span>
              <MdInline text={criterion.text} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TrailList({ trail }: { trail: KanbanTrailEntry[] }) {
  return (
    <div>
      <p className="m-0 mb-2 flex items-center gap-1.5 border-b border-border pb-1.5 font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
        <ClockGlyph className="size-3" />
        Trail
      </p>
      <ul className="m-0 grid list-none gap-1 p-0">
        {trail.map((entry, index) => (
          <li
            key={`${entry.date}-${entry.ref}-${index}`}
            className="flex flex-wrap items-baseline gap-x-2 text-xs leading-5"
          >
            {entry.date ? (
              <span className="shrink-0 font-mono text-muted-foreground">
                {entry.date}
              </span>
            ) : null}
            {entry.actor ? (
              <span className="font-medium text-foreground">{entry.actor}</span>
            ) : null}
            {/* The ref is the one identifier a session already produced —
                a sha, a PR number — and it renders as that identifier. It
                used to resolve to a hosting-provider URL; a sha is already
                the address, and `git show` takes it. */}
            {entry.ref ? (
              <span className="font-mono text-muted-foreground">
                {entry.ref}
              </span>
            ) : null}
            {entry.note ? (
              <span className="text-muted-foreground">
                <MdInline text={entry.note} />
              </span>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  )
}

function BoardCard({
  card,
  interactive,
  compact,
  dragging,
  onDragStart,
  onDragEnd,
  onOpen,
}: {
  card: IdentifiedCard
  interactive: boolean
  compact: boolean
  dragging: boolean
  onDragStart: (uid: string, event: React.DragEvent) => void
  onDragEnd: () => void
  onOpen: (uid: string) => void
}) {
  // Cardfile-v2 fields are absent from data generated by older folio
  // builds, so every access is guarded; v1 cards render exactly as before.
  const blockedBy = card.blocked_by ?? []
  const criteria = card.criteria ?? []
  const doneCriteria = criteria.filter((criterion) => criterion.done).length

  if (compact) {
    return (
      <div
        role="listitem"
        data-slot="kanban-card"
        data-card={card.uid}
        data-dragging={dragging ? "" : undefined}
        draggable={interactive}
        onDragStart={(event) => onDragStart(card.uid, event)}
        onDragEnd={onDragEnd}
        className={cn(
          "group/card relative m-0 min-w-0 rounded-md border border-border bg-card p-2.5 transition-opacity",
          interactive && "cursor-grab active:cursor-grabbing",
          "data-dragging:opacity-40"
        )}
      >
        {card.priority === "high" ? (
          <>
            <span
              aria-hidden="true"
              className="absolute inset-y-1.5 -left-px w-px bg-destructive"
            />
            <span className="sr-only">High priority</span>
          </>
        ) : null}

        <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
          <CardTitle card={card} />
        </div>

        {card.tags.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {card.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md border border-border bg-muted/35 px-1 font-mono text-xs leading-4 font-medium text-muted-foreground"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        {blockedBy.length > 0 || criteria.length > 0 ? (
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {blockedBy.length > 0 ? (
              <span className="inline-flex items-center rounded-md border border-warning/55 bg-warning/10 px-1 font-mono text-xs leading-4 font-semibold tracking-[0.08em] text-warning uppercase">
                blocked
                <span className="sr-only">{` by ${blockedBy.join(", ")}`}</span>
              </span>
            ) : null}
            {criteria.length > 0 ? (
              <span className="inline-flex items-center gap-1 rounded-md border border-border bg-muted/35 px-1 font-mono text-xs leading-4 text-muted-foreground">
                <CheckGlyph className="h-2.5 w-2.5" />
                {doneCriteria}/{criteria.length}
                <span className="sr-only"> acceptance criteria done</span>
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    )
  }

  // Full boards keep the card to its title; everything else — description,
  // criteria, trail, artifacts, metadata — lives in the dialog that opens
  // on click.
  return (
    <div
      role="listitem"
      data-slot="kanban-card"
      data-card={card.uid}
      data-dragging={dragging ? "" : undefined}
      draggable={interactive}
      onDragStart={(event) => onDragStart(card.uid, event)}
      onDragEnd={onDragEnd}
      className={cn(
        "group/card relative m-0 min-w-0 rounded-lg border border-border bg-card px-4 pt-3.5 pb-3.5 transition-colors",
        "hover:border-muted-foreground data-dragging:opacity-40",
        interactive && "cursor-grab active:cursor-grabbing"
      )}
    >
      {/* The milestone is the card's first line now, not a number hiding in
          the corner the move buttons want. It reads as the landing's
          eyebrow; the dialog's milestone row is where it goes somewhere. */}
      <CardKey card={card} />

      <button
        type="button"
        aria-haspopup="dialog"
        onClick={() => onOpen(card.uid)}
        className={cn(
          "block w-full text-left text-base leading-6 font-semibold text-foreground transition-colors hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
          (card.type || card.milestone) && "mt-1.5"
        )}
      >
        {card.title}
      </button>

      {card.icon || card.priority || card.assignee.length > 0 || card.size ? (
        <p className="m-0 mt-2.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] leading-4 tracking-[0.04em] text-muted-foreground">
          {card.icon ? (
            /* The category as a pill — icon plus the tag that brought it,
               in the meta row at the row's own scale. */
            <span className="rounded-md border border-border bg-muted/35 px-1.5 font-medium">
              <span aria-hidden="true">{card.icon}</span> {card.iconTag}
            </span>
          ) : null}
          {card.assignee.map((name) => (
            <span key={name}>@{name}</span>
          ))}
          {card.priority ? (
            /* Only a spelled-out priority draws a chip — most cards omit
               the field, and a chip on every card would say nothing. The
               tones are the dialog's Priority field at row scale: high in
               the warning ink, low faded, an explicit normal neutral. */
            <span
              className={cn(
                "ml-auto rounded-md border px-1 font-medium",
                card.priority === "high"
                  ? "border-destructive/45 bg-destructive/10 text-destructive"
                  : card.priority === "low"
                    ? "border-border bg-muted/40 text-muted-foreground"
                    : "border-border bg-card text-foreground"
              )}
            >
              {card.priority}
              <span className="sr-only"> priority</span>
            </span>
          ) : null}
          {card.size ? (
            <span
              className={cn(
                "rounded-md border border-border bg-muted/35 px-1 font-medium",
                !card.priority && "ml-auto"
              )}
            >
              {card.size}
              <span className="sr-only"> size</span>
            </span>
          ) : null}
        </p>
      ) : null}
    </div>
  )
}

/* The card's column, as a field you set.

   This was the board's last native select element, kept for three reasons the
   custom shape now answers one by one. Focus across the move: picking a
   column reparents the card on the BOARD, not in this aside — the trigger
   button is the same DOM node before and after, so it keeps focus exactly
   as the select did (the peril that killed the old face MoveButtons was
   theirs alone). Semantics: the APG select-only combobox carries role,
   value, position, arrows and Home/End explicitly. Touch above clipping
   ancestors: the one real loss — the OS drew its picker over the dialog's
   `overflow-y-auto` body, the absolute panel cannot — is answered the way
   the composer rail answers it, `scrollIntoView` on open.

   When the board is not interactive — the server render, and the first
   client frame before the overlay mounts — the same slot renders the
   column as plain text, so status is a field in the static export too,
   not something that appears at hydration. */
function StatusField({
  card,
  columns,
  columnIndex,
  canMove,
  onMove,
}: {
  card: IdentifiedCard
  columns: BoardColumn[]
  columnIndex: number
  canMove: boolean
  onMove: (targetColumn: number) => void
}) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(columnIndex)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const panelRef = useRef<HTMLDivElement | null>(null)
  const listId = `${useId().replace(/:/g, "")}-status`
  const current = columns[columnIndex]

  // Open: seed the active row to where the card is, and walk the panel
  // into view — the aside scrolls with the dialog body, and a panel that
  // opens under its fold is a menu nobody sees.
  useEffect(() => {
    if (open) {
      panelRef.current?.scrollIntoView({ block: "nearest" })
    }
  }, [open])
  useEffect(() => {
    if (open) {
      panelRef.current
        ?.querySelector("[data-active]")
        ?.scrollIntoView({ block: "nearest" })
    }
  }, [open, active])
  useEffect(() => {
    if (!open) {
      return
    }
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", onPointer)
    return () => document.removeEventListener("mousedown", onPointer)
  }, [open])

  if (!canMove || !current) {
    return (
      <div className="mb-5">
        <span className="mb-1 block font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
          Status
        </span>
        <span className="flex items-center gap-2 text-sm text-foreground">
          <span
            aria-hidden="true"
            className="size-2 shrink-0 rounded-[2px] border border-foreground/50 bg-accent"
          />
          {current?.title ?? "\u2014"}
        </span>
      </div>
    )
  }

  const close = (refocus: boolean) => {
    setOpen(false)
    if (refocus) {
      triggerRef.current?.focus()
    }
  }
  const openPanel = () => {
    setActive(columnIndex)
    setOpen(true)
    /* The trigger prevents mousedown default (the Safari focusout dance),
       so a mouse open leaves focus wherever it was — on the dialog's
       close button, usually. Escape would then target that button, the
       root's cage would never see it, and the whole dialog died with the
       panel open. Focus is moved by hand so the cage always has the key. */
    triggerRef.current?.focus()
  }
  const pick = (index: number) => {
    if (index !== columnIndex) {
      onMove(index)
    }
    close(true)
  }

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (!open) {
      if (
        event.key === "Enter" ||
        event.key === " " ||
        event.key === "ArrowDown"
      ) {
        event.preventDefault()
        openPanel()
      }
      return
    }
    if (event.key === "Escape") {
      /* Escape belongs to the open panel first, and the dialog's own
         dismiss listener sits on `document` — the same target React
         delegates to, where stopPropagation() suppresses nothing. The
         combobox cage, verbatim: stopImmediatePropagation cancels the
         later-registered dialog listener, preventDefault sets the flag
         that listener early-returns on, and stopPropagation stays for
         non-document embed topologies. */
      event.preventDefault()
      event.stopPropagation()
      event.nativeEvent.stopImmediatePropagation()
      close(true)
      return
    }
    if (event.key === "ArrowDown") {
      event.preventDefault()
      setActive(Math.min(active + 1, columns.length - 1))
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      setActive(Math.max(active - 1, 0))
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault()
      setActive(event.key === "Home" ? 0 : columns.length - 1)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      pick(active)
    }
  }

  return (
    <div
      ref={rootRef}
      className="relative mb-5"
      onKeyDown={onKeyDown}
      onBlur={(event) => {
        /* Tab can walk away with the panel painted; close without refocus
           when focus settles outside the root. Mouse picks never blur:
           the rows preventDefault on mousedown. */
        if (
          open &&
          !rootRef.current?.contains(event.relatedTarget as Node | null)
        ) {
          close(false)
        }
      }}
    >
      <span className="mb-1.5 block font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
        Move to
      </span>
      {/* The drawn value the select used to hide behind, now the control
          itself: the board's last native menu joins the combobox family.
          The trigger is the same node before and after a move, so focus
          survives the card's reparenting exactly as the select's did. */}
      <button
        type="button"
        ref={triggerRef}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-activedescendant={open ? `${listId}-${active}` : undefined}
        aria-label="Move to"
        onMouseDown={(event) => event.preventDefault()}
        onClick={() => (open ? close(true) : openPanel())}
        className="flex h-10 w-full cursor-pointer items-center justify-between gap-2 rounded-md border border-border bg-card px-3 transition-colors hover:border-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      >
        <span className="flex min-w-0 items-center gap-2">
          <span
            aria-hidden="true"
            className="size-2 shrink-0 rounded-[2px] border border-foreground/50 bg-accent"
          />
          <span className="truncate text-sm text-foreground">
            {current.title}
          </span>
        </span>
        <ChevronDownGlyph className="size-4 shrink-0 text-muted-foreground" />
      </button>
      {open ? (
        <div
          ref={panelRef}
          onMouseDown={(event) => event.preventDefault()}
          className="absolute inset-x-0 z-20 mt-1 overflow-hidden rounded-md border border-border bg-card shadow-lg"
        >
          <ul
            role="listbox"
            id={listId}
            aria-label="Move to"
            className="m-0 max-h-56 list-none overflow-y-auto p-1"
          >
            {columns.map((column, index) => (
              <li
                key={column.id}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === columnIndex}
                data-active={index === active ? "" : undefined}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => pick(index)}
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-sm",
                  index === active
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground"
                )}
              >
                <span className="truncate">{column.title}</span>
                {/* The count the column header already shows, at the moment
                    it matters most: over-limit ink warns before the move
                    that would worsen it. */}
                <span
                  className={cn(
                    "shrink-0 font-mono text-[10px]",
                    column.limit !== null && column.cards.length > column.limit
                      ? "text-warning"
                      : "text-muted-foreground"
                  )}
                >
                  {column.limit !== null
                    ? `${column.cards.length}/${column.limit}`
                    : column.cards.length}
                  {column.limit !== null &&
                  column.cards.length > column.limit ? (
                    // The header's WipBadge says this in words too; an
                    // option named "10/3" alone reads as a fraction, not
                    // a warning.
                    <span className="sr-only"> cards, over the limit</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <span aria-live="polite" className="sr-only">
        {`"${card.title}" is in ${current.title}.`}
      </span>
    </div>
  )
}

/* The complete card, opened by clicking its title on the board. Rendered
   as a modal dialog so the board stays one instance: no per-card routes,
   no second board. Focus is trapped inside it — without that, Tab reaches
   the filter field behind the overlay, and typing there changes which
   cards exist while the dialog is open. */
function CardDetail({
  card,
  columns,
  columnIndex,
  canMove,
  canAttach,
  moveCommand,
  roadmapHref,
  onMove,
  onClose,
  initialArtifact,
}: {
  card: IdentifiedCard
  columns: BoardColumn[]
  columnIndex: number
  canMove: boolean
  /** Whether artifact attachment is enabled. `canMove` is broader: any
   * hydrated board can stage a drag. */
  canAttach: boolean
  moveCommand: string
  roadmapHref?: string
  onMove: (targetColumn: number) => void
  onClose: () => void
  /** Artifact target restored from the URL: the board resolved it before
   * opening this dialog, and the drawer opens with it. */
  initialArtifact?: string | null
}) {
  const titleId = `${useId().replace(/:/g, "")}-title`
  // The trap encloses the wrapper, not the dialog frame: the drawer is the
  // frame's sibling, and Tab walks both as one layer while it is open.
  const wrapperRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const bandRef = useRef<HTMLDivElement>(null)
  const readerOpenerRef = useRef<HTMLElement | null>(null)
  // The drawer: which artifact is being read, by band index, and at which
  // width. Restored from the URL once, on mount — the deep link promised a
  // reading position, and the dialog opened to honor it.
  const [reading, setReading] = useState<{
    index: number
    wide: boolean
  } | null>(() => {
    if (!initialArtifact) {
      return null
    }
    const artifacts = card.artifacts ?? []
    const index = artifacts.findIndex(
      (entry) => entry.target === initialArtifact
    )
    const mode = index >= 0 ? readerMode(artifacts[index]) : null
    return mode ? { index, wide: mode === "asset" } : null
  })
  // Mirrored for the document-level key handler, which must not
  // re-subscribe per reading change.
  const readingRef = useRef(reading)
  useEffect(() => {
    readingRef.current = reading
  }, [reading])

  // The reading position is a URL: ?card= and ?artifact= restore the
  // dialog and the drawer on load. Same replaceState idiom as the filter's
  // writeQueryUrl, built from the current location so the filter's own
  // parameters survive — only these two are ours to remove. The hash goes
  // with them: it names a heading in the document that is opening or
  // closing, never anything of the board's.
  const writeReaderUrl = useCallback(
    (target: string | null) => {
      try {
        const url = new URL(window.location.href)
        url.searchParams.delete("card")
        url.searchParams.delete("artifact")
        url.hash = ""
        if (target) {
          url.searchParams.set("card", card.uid)
          url.searchParams.set("artifact", target)
        }
        window.history.replaceState(null, "", `${url.pathname}${url.search}`)
      } catch {
        // History unavailable: the drawer still opens.
      }
    },
    [card.uid]
  )

  const openReader = useCallback(
    (index: number, opener: HTMLElement | null) => {
      const artifact = (card.artifacts ?? [])[index]
      const mode = artifact ? readerMode(artifact) : null
      if (!mode) {
        return
      }
      readerOpenerRef.current = opener
      // Prototypes were built for a full window; documents want a measure.
      setReading({ index, wide: mode === "asset" })
      writeReaderUrl(artifact.target)
    },
    [card.artifacts, writeReaderUrl]
  )

  const closeReader = useCallback(() => {
    setReading(null)
    writeReaderUrl(null)
    // Focus returns to the tile that opened the reading; a deep link never
    // had one, and lands on the band it would have come from.
    const opener = readerOpenerRef.current
    readerOpenerRef.current = null
    if (opener && document.contains(opener)) {
      opener.focus()
    } else {
      bandRef.current?.focus()
    }
  }, [writeReaderUrl])

  // Closing the dialog closes the reading with it; the URL lets go too.
  // On the close action, not on unmount: an unmount cleanup also runs in
  // the dev-mode mount rehearsal, which wiped a deep link before the
  // drawer it named had finished opening.
  const closeDialog = useCallback(() => {
    if (readingRef.current) {
      writeReaderUrl(null)
    }
    onClose()
  }, [onClose, writeReaderUrl])
  // Which regions scroll is a breakpoint fact, and the tab stops follow
  // it: below md the body grid is one scrolling stack (one stop), at md+
  // the prose and the rail scroll apart (two stops). Leaving all three
  // focusable put one or two dead stops — focusable, scrolling nothing —
  // on the keyboard path to the content at every width. Post-hydration
  // read, same idiom as the toolbar's narrow flag.
  const [splitScroll, setSplitScroll] = useState(false)
  useEffect(() => {
    const query = window.matchMedia("(min-width: 768px)")
    const sync = () => setSplitScroll(query.matches)
    sync()
    query.addEventListener("change", sync)
    return () => query.removeEventListener("change", sync)
  }, [])

  useEffect(() => {
    const opener =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null
    // A deep link opened the drawer with the dialog; focus belongs in the
    // drawer then, and the reader has already taken it.
    if (!readingRef.current) {
      closeRef.current?.focus()
    }
    const handleKey = (event: KeyboardEvent) => {
      /* A control inside the dialog that consumed this key — the open
         Move-to panel's Escape — marks it with preventDefault. Same belt
         the rail's listener wears: stopImmediatePropagation alone only
         works because React hydrated first, and belts are cheap. */
      if (event.defaultPrevented) {
        return
      }
      if (event.key === "Escape") {
        // One press, one level: the drawer first, then the dialog.
        if (readingRef.current) {
          closeReader()
          return
        }
        closeDialog()
        return
      }
      if (event.key !== "Tab" || !wrapperRef.current) {
        return
      }
      const focusable = wrapperRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
      if (focusable.length === 0) {
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      const active = document.activeElement
      // Focus outside the layer is pulled back in whichever way Tab is
      // travelling: the board behind the overlay must stay unreachable,
      // filter field included.
      const outside = !wrapperRef.current.contains(active)
      if (event.shiftKey && (active === first || outside)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (active === last || outside)) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener("keydown", handleKey)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      document.removeEventListener("keydown", handleKey)
      document.body.style.overflow = previousOverflow
      opener?.focus()
    }
  }, [closeDialog, closeReader])

  const blockedBy = card.blocked_by ?? []
  const criteria = card.criteria ?? []
  const artifacts = card.artifacts ?? []
  const trail = card.trail ?? []
  const comments = card.comments ?? []

  // What the description's `./` links resolve against. onOpen is the
  // openReader above — a document link in the prose reads in the drawer,
  // exactly like its tile in the band below.
  const bodyLinks: CardLinkContext = {
    cardId: card.id ?? "",
    artifacts,
    onOpen: openReader,
  }

  const fields: [string, React.ReactNode][] = [
    [
      "Milestone",
      // The same link the card carries. A milestone names a roadmap step,
      // and the dialog is where you have just read enough about the card to
      // want it — printing it as plain text made you go back to the board
      // to click the one on the card.
      card.milestone ? (
        roadmapHref && card.phase ? (
          <a
            href={`${roadmapHref}#${card.phase}`}
            className="rounded-sm text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            {card.phaseTitle
              ? `${card.phaseTitle} · ${card.milestone}`
              : card.milestone}
          </a>
        ) : (
          card.milestone
        )
      ) : (
        "—"
      ),
    ],
    [
      "Tags",
      card.tags.length > 0 ? (
        <span className="flex flex-wrap gap-1">
          {card.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-md border border-border bg-accent/40 px-1.5 text-xs leading-4 text-foreground"
            >
              {tag}
            </span>
          ))}
        </span>
      ) : (
        "—"
      ),
    ],
    [
      "Priority",
      // Priority is a judgement about the card, not a fact about it, and it
      // was the same grey as the created date sitting under it. Only the
      // ends of the scale get a colour: a board where every card is tinted
      // says nothing.
      card.priority ? (
        <span
          className={cn(
            "inline-flex items-center rounded-md border px-1.5 text-xs leading-5",
            card.priority === "high"
              ? "border-destructive/45 bg-destructive/10 font-medium text-destructive"
              : card.priority === "low"
                ? "border-border bg-muted/40 text-muted-foreground"
                : "border-border bg-card text-foreground"
          )}
        >
          {card.priority}
        </span>
      ) : (
        "normal"
      ),
    ],
  ]
  if (card.type) {
    fields.splice(1, 0, ["Type", card.type])
  }
  if (card.size) {
    fields.push([
      "Size",
      <span
        key="size-value"
        className="inline-flex items-center rounded-md border border-border bg-card px-1.5 text-xs leading-5"
      >
        {card.size}
      </span>,
    ])
  }
  if (card.assignee.length > 0) {
    fields.push(["Assignee", card.assignee.map((name) => `@${name}`).join(" ")])
  }
  if (card.source) {
    fields.push([
      "Source",
      /^https?:\/\//.test(card.source) ? (
        <a
          key="source-value"
          href={card.source}
          className="rounded-sm text-primary underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          {card.source}
        </a>
      ) : (
        card.source
      ),
    ])
  }
  if (card.created) {
    fields.push(["Created", card.created])
  }
  if (card.parent) {
    fields.push(["Parent", card.parent])
  }
  if (blockedBy.length > 0) {
    // The one entry in this column that means the card cannot proceed, and
    // it read as a grey comma list between the assignee and the created
    // date. Each blocker is its own chip because each is a card id you go
    // and look at.
    fields.push([
      "Blocked by",
      <span key="blocked-by-value" className="flex flex-wrap gap-1">
        {blockedBy.map((blocker) => (
          <span
            key={blocker}
            className="rounded-md border border-warning/50 bg-warning/10 px-1.5 font-mono text-xs leading-5 text-warning"
          >
            {blocker}
          </span>
        ))}
      </span>,
    ])
  }
  if (card.id) {
    // "Every card is a file" is the board's whole claim, and this row is
    // where it is shown rather than asserted: the path is the modification
    // path. On a published board the browser writes nothing, so "where do
    // I change this" has to be answerable from the card, and the answer is
    // a file. It presided over the header for a while; the title owns that
    // strip now, and a fact about the card sits with the other facts.
    fields.push([
      "Card",
      <span
        key="card-value"
        className="inline-flex min-w-0 items-center gap-1.5"
      >
        <FileGlyph className="size-3.5 shrink-0" />
        {/* The path the build resolved, which honours a `source:` that is
            not `board/`. The old hard-coded string was right for this
            repository and wrong for every other one. */}
        <span className="break-all">
          {card.file || `board/cards/${card.id}.md`}
        </span>
      </span>,
    ])
  }

  return (
    <div
      ref={wrapperRef}
      data-slot="kanban-card-dialog"
      className="fixed inset-0 z-50 flex items-center justify-center bg-scrim/55 p-4 backdrop-blur-[1px]"
      onClick={(event) => {
        // The dim rim closes the top layer, like Escape: the drawer first.
        if (event.target === event.currentTarget) {
          if (readingRef.current) {
            closeReader()
          } else {
            closeDialog()
          }
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        /* Bigger. It was 1024px and 90vh, which put a card with a long
           description and a few trail lines into a scroll inside a modal —
           the one shape that hides how much is left. The measure that
           matters is the prose column, and that is capped where it reads;
           the extra width goes to the rail and the extra height to not
           scrolling. */
        className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl"
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-border px-8 py-4">
          {/* The title presides. The strip used to open on the card's file
              path — a fact about where the card lives, ahead of what the
              card is about. The path still answers "where do I change
              this", as the Card field in the rail, link and all. */}
          <h2
            id={titleId}
            className="m-0 min-w-0 text-[22px] leading-[30px] font-bold tracking-[-0.015em] text-balance text-foreground"
          >
            {card.title}
          </h2>
          {/* Two marks, one 28px height: the hint and the close. A pen sat
              between them and opened the repository host's web editor,
              which is not where anyone edits and is the wrong place
              entirely for a board hosted elsewhere. Editing is local: the
              Card field in the rail names the file, and `folio kanban`
              writes it. A control that cannot do the thing it draws is
              worse than no control. */}
          <span className="flex shrink-0 items-center gap-2 pt-0.5">
            <kbd className="flex h-7 items-center rounded border border-border bg-background px-1.5 font-mono text-xs text-muted-foreground">
              Esc
            </kbd>
            <button
              ref={closeRef}
              type="button"
              onClick={closeDialog}
              aria-label="Close card"
              className="flex size-7 shrink-0 items-center justify-center rounded-md border border-border bg-background text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              <CloseGlyph className="size-3.5" />
            </button>
          </span>
        </div>

        {/* The card body scrolls, so it is a tab stop. Without tabIndex a
            keyboard user can only reach whatever links happen to sit
            inside it: a long trail below the fold is unreachable, and a
            card with no links is completely unscrollable.

            At md the scroll splits in two: the prose and the rail are
            different lengths, and one shared scroll dragged the facts off
            screen while you were still reading the description. Each
            column owns its scroll there — and each is its own tab stop,
            for exactly the reason the container is one below md. The row
            is clamped to the container (minmax(0,1fr)), or an auto row
            would size to the taller column and overflow unscrollably. */}
        <div
          tabIndex={splitScroll ? -1 : 0}
          role="group"
          aria-label="Card body"
          className="grid min-h-0 overflow-y-auto focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring md:grid-cols-[1fr_20rem] md:grid-rows-[minmax(0,1fr)] md:overflow-y-hidden"
        >
          <div
            tabIndex={splitScroll ? 0 : -1}
            role="group"
            aria-label="Card prose"
            className="min-w-0 px-8 py-7 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring md:overflow-y-auto"
          >
            {card.description ? (
              /* The card is a markdown file and this is its prose, block
                 by block: paragraphs read as paragraphs, lists read as
                 lists, and the inline marks render instead of showing
                 their asterisks. */
              <div className="mb-7 max-w-[70ch] text-base leading-7 break-words text-muted-foreground">
                {parseMdBlocks(card.description).map((block, index) =>
                  block.kind === "list" ? (
                    block.ordered ? (
                      <ol
                        key={index}
                        className="mt-0 mb-4 list-decimal pl-5 marker:text-muted-foreground/60 last:mb-0"
                      >
                        {block.items.map((item, itemIndex) => (
                          <li key={itemIndex} className="mb-1 last:mb-0">
                            <MdInline text={item} links={bodyLinks} />
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <ul
                        key={index}
                        className="mt-0 mb-4 list-disc pl-5 marker:text-muted-foreground/60 last:mb-0"
                      >
                        {block.items.map((item, itemIndex) => (
                          <li key={itemIndex} className="mb-1 last:mb-0">
                            <MdInline text={item} links={bodyLinks} />
                          </li>
                        ))}
                      </ul>
                    )
                  ) : (
                    <p key={index} className="mt-0 mb-4 last:mb-0">
                      <MdInline text={block.text} links={bodyLinks} />
                    </p>
                  )
                )}
              </div>
            ) : null}

            {criteria.length > 0 ? <CriteriaList criteria={criteria} /> : null}

            {trail.length > 0 ? (
              <div className={cn(criteria.length > 0 && "mt-5")}>
                <TrailList trail={trail} />
              </div>
            ) : null}

            {card.link ? (
              <p className="mt-5 mb-0 text-sm">
                <a
                  href={card.link}
                  className="text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground"
                >
                  Open linked page
                </a>
              </p>
            ) : null}
          </div>

          <aside
            /* Same contract as the prose column: it scrolls on its own at
               md, and on a static export it can hold zero focusables, so
               the stop is what keeps a long rail keyboard-reachable. */
            tabIndex={splitScroll ? 0 : -1}
            role="group"
            aria-label="Card facts"
            className="border-t border-border bg-background px-7 py-7 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring md:overflow-y-auto md:border-t-0 md:border-l"
          >
            {/* The one decision, then the facts.

                It has lived in three places. In the rail as the sixth
                label-over-value row, where it looked exactly like the five
                readings it sits above and only a small chevron said
                otherwise. Then in the header, glued to the end of a mono
                file path, reading as that path's last segment, in the strip
                that identifies the card rather than changes it.

                It is back at the head of the rail, and it is the only thing
                in this column with a surface, a border, a 40px height, and
                a label in the accent that says what pressing it does rather
                than naming a field. One box against five bare rows: you can
                see which one you can touch before reading a word. */}
            <StatusField
              card={card}
              columns={columns}
              columnIndex={columnIndex}
              canMove={canMove}
              onMove={onMove}
            />
            {fields.map(([key, value]) => (
              <div key={key} className="mb-3 last:mb-0">
                <span className="mb-1 block font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
                  {key}
                </span>
                <span className="block text-xs break-words text-foreground">
                  {value}
                </span>
              </div>
            ))}
          </aside>
        </div>

        {/* The thread before the attachments, the way a mail carries its
            replies before its files. Comments are conversation — the trail
            up in the prose is the record — so they get their own separated
            band, same scroll cap and keyboard stop as the artifacts below.
            No comments, no band: a mail without replies shows no empty
            thread. */}
        {comments.length > 0 ? (
          <div
            tabIndex={0}
            role="group"
            aria-label="Comments"
            className="max-h-44 shrink-0 overflow-y-auto border-t border-border px-8 py-4 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
          >
            <p className="m-0 mb-2.5 flex items-center gap-1.5 font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
              <BubbleGlyph className="size-3" />
              {`Comments · ${comments.length}`}
            </p>
            <ul className="m-0 grid list-none gap-2.5 p-0">
              {comments.map((comment, index) => (
                <li
                  key={`${comment.date}-${comment.actor}-${index}`}
                  className="border-l-2 border-border pl-3"
                >
                  <p className="m-0 flex flex-wrap items-baseline gap-x-2 font-mono text-xs leading-5 text-muted-foreground">
                    {comment.date ? <span>{comment.date}</span> : null}
                    {comment.actor ? (
                      <span className="font-medium text-foreground">
                        @{comment.actor}
                      </span>
                    ) : null}
                  </p>
                  <p className="m-0 max-w-[70ch] text-sm leading-6 break-words text-foreground">
                    <MdInline text={comment.text} />
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Attachments close the card the way they close a mail: a band
            across the full width, under the prose. They lived at the bottom
            of the rail as grey chips and read as one more fact; but the doc
            a card produced and the PR that carries it are the card's
            output, and output gets the floor. The band sits outside the
            body's scroll, so it caps its own height and scrolls itself
            rather than clipping under the dialog's overflow-hidden. The
            dashed tile teaches the gesture — the browser never writes a
            card, the CLI does. */}
        {artifacts.length > 0 || (canAttach && card.id) ? (
          <div
            ref={bandRef}
            /* Same deal as the card body above: a scroll container is a tab
               stop, or a keyboard cannot scroll it when every tile inside
               is a plain span (no repo configured → no anchors). */
            tabIndex={0}
            role="group"
            aria-label="Artifacts"
            className="max-h-44 shrink-0 overflow-y-auto border-t border-border px-8 py-4 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
          >
            <p className="m-0 mb-2 flex items-center gap-1.5 font-mono text-xs tracking-[0.08em] text-muted-foreground uppercase">
              <PaperclipGlyph className="size-3" />
              {artifacts.length > 0
                ? `Artifacts · ${artifacts.length}`
                : "Artifacts"}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              {artifacts.map((artifact, index) => (
                <ArtifactTile
                  key={`${artifact.kind}-${artifact.target}-${index}`}
                  artifact={artifact}
                  current={reading?.index === index}
                  onOpen={
                    readerMode(artifact)
                      ? (opener) => openReader(index, opener)
                      : undefined
                  }
                />
              ))}
              {canAttach && card.id ? (
                <span className="inline-flex min-w-0 items-center rounded-md border border-dashed border-border px-2.5 py-1.5 text-xs text-muted-foreground">
                  + attach
                  <code className="ml-1.5 font-mono text-[11px] break-all">
                    {`folio kanban attach ${card.id} --doc <path>`}
                  </code>
                </span>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* The footer carries the consequence, and only when there is
            one. When this card is staged somewhere the repository does
            not have it, the exact line `Export moves` will write is
            printed here, character for character — the board's whole
            claim is that every card is a file and the browser never
            writes one, and this is the one place that can be shown
            rather than asserted. An unstaged card used to get a
            placeholder sentence instead; that was a strip of chrome
            explaining a feature nobody had used yet, and the owner asked
            what it was — which is the review. */}
        {canMove && moveCommand ? (
          <div className="shrink-0 border-t border-border px-8 py-4">
            <code className="font-mono text-xs break-all text-foreground">
              {moveCommand}
            </code>
          </div>
        ) : null}
      </div>

      {/* The drawer paints over the frame where they overlap (later
          sibling), and the frame stays live beside it: the band is still
          clickable, so switching artifacts never means closing first. */}
      {reading && artifacts[reading.index] ? (
        <ArtifactReader
          artifact={artifacts[reading.index]}
          wide={reading.wide}
          onToggleWide={() =>
            setReading((open) => (open ? { ...open, wide: !open.wide } : open))
          }
          onClose={closeReader}
        />
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Board                                                                */
/* ------------------------------------------------------------------ */

export function KanbanBoard({
  columns = kanbanColumns,
  compact = false,
  maxCardsPerColumn,
  title,
  description,
  roadmapHref,
  workspace = false,
}: {
  columns?: KanbanColumn[]
  compact?: boolean
  maxCardsPerColumn?: number
  /** On a dedicated board page the layout renders no band, so the board
   * carries its own masthead. Embedded boards pass none of this. */
  title?: string
  description?: string
  /** Where the roadmap lives relative to this page. A card's milestone
   * links to the step it names, which is the return path for the roadmap's
   * own ?milestone= link into the board. Absent when the roadmap has no
   * public route, in which case the milestone renders as plain text. */
  roadmapHref?: string
  /** The standalone public page (/kanban) is an app, not a document: at
   * lg+ the section takes exactly the viewport below the navbar, the
   * composer rail becomes a full-height panel with its own scroll, and
   * the columns scroll on both axes inside the canvas. Only the plugin's
   * emitted view page sets this; a board embedded in docs prose keeps the
   * in-flow layout this prop defaults to. Below lg nothing changes — the
   * rail is the same fixed drawer either way. */
  workspace?: boolean
}) {
  const baseline = useMemo(() => identify(columns), [columns])
  // The overlay is keyed by the column set, not by the whole board: a card
  // edited or added upstream no longer discards staged moves, because each
  // entry carries its own staleness check.
  const storageKey = useMemo(
    () =>
      `folio-kanban:${sourceHash(baseline.map((column) => column.id).join("|"))}`,
    [baseline]
  )

  const [board, setBoard] = useState<BoardColumn[]>(baseline)
  const [interactive, setInteractive] = useState(false)
  // Starts false so the server markup and the first client render agree;
  // the phone-sized placeholder arrives a frame later, which is the same
  // deal `interactive` takes. `sm` is Tailwind's 640px, the width the rest
  // of this toolbar already changes at.
  const [narrowToolbar, setNarrowToolbar] = useState(false)
  // The composer beside the board. Open by default on a wide screen would
  // spend a third of the surface before anyone asked; it opens on request
  // and remembers nothing, because the filter it writes is in the URL.
  const [panelOpen, setPanelOpen] = useState(false)
  useEffect(() => {
    const query = window.matchMedia("(max-width: 639px)")
    const sync = () => setNarrowToolbar(query.matches)
    sync()
    query.addEventListener("change", sync)
    return () => query.removeEventListener("change", sync)
  }, [])
  // How many cards sit somewhere other than where the repository has them.
  // "Some moves are staged" is the state people lose track of, so the sync
  // line says the number.
  const [stagedCount, setStagedCount] = useState(0)
  // Derived, not stored. It was a second useState set on the line above
  // every setStagedCount, which is two names for one fact and a standing
  // obligation to keep them in step.
  const dirty = stagedCount > 0
  const [dragUid, setDragUid] = useState<string | null>(null)
  const [dropTarget, setDropTarget] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)
  const [query, setQuery] = useState("")
  const [selectedUid, setSelectedUid] = useState<string | null>(null)
  // The artifact target a ?card=&?artifact= deep link asked to read,
  // handed to the dialog once and cleared when it closes; the dialog owns
  // the reading from there.
  const [restoredArtifact, setRestoredArtifact] = useState<string | null>(null)
  // A live region only re-announces when its text changes, so two identical
  // messages in a row would be silent. The counter keys the node, which
  // forces the announcement every time.
  const [announcement, setAnnouncement] = useState({ text: "", seq: 0 })
  const instanceId = useId().replace(/:/g, "")
  const descriptionId = `${instanceId}-description`
  const dragRef = useRef<string | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  // The field, for deciding what counts as a press outside the reference.
  const syntaxRef = useRef<HTMLDivElement>(null)
  const sectionRef = useRef<HTMLElement>(null)
  const railRef = useRef<HTMLDivElement | null>(null)
  const filterToggleRef = useRef<HTMLButtonElement | null>(null)
  const signatureRef = useRef("")

  const announceTimer = useRef<number | null>(null)

  // A discrete action — a move, a reset — is worth speaking the moment it
  // happens.
  const announce = useCallback((text: string) => {
    if (announceTimer.current !== null) {
      window.clearTimeout(announceTimer.current)
      announceTimer.current = null
    }
    setAnnouncement((previous) => ({ text, seq: previous.seq + 1 }))
  }, [])

  // Filtering is not discrete: it fires on every keystroke, and because the
  // live region is keyed by `seq` it re-reads even when the text repeats.
  // Typing a six-character query queued six announcements — four of them
  // identical — over the field's own echo. The result is only worth
  // speaking once the typing stops.
  const announceSettled = useCallback((text: string) => {
    if (announceTimer.current !== null) {
      window.clearTimeout(announceTimer.current)
    }
    announceTimer.current = window.setTimeout(() => {
      announceTimer.current = null
      setAnnouncement((previous) => ({ text, seq: previous.seq + 1 }))
    }, 600)
  }, [])

  useEffect(
    () => () => {
      if (announceTimer.current !== null) {
        window.clearTimeout(announceTimer.current)
      }
    },
    []
  )

  // Load the saved overlay after mount (SSG markup always shows the git
  // baseline, so hydration stays clean). Deferred through
  // requestAnimationFrame so the state updates happen outside the effect
  // body (same idiom as ProjectHeaderActions' mounted flag).
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      try {
        const raw = window.localStorage.getItem(storageKey)
        if (raw) {
          const saved = JSON.parse(raw) as Overlay
          if (saved && typeof saved === "object" && !Array.isArray(saved)) {
            const { board: restored, applied } = applyOverlay(baseline, saved)
            if (applied > 0) {
              setBoard(restored)
              setStagedCount(applied)
            }
          }
        }
      } catch {
        // Corrupt overlay: fall back to the baseline.
      }
      // ?milestone= / ?tag= / ?q= pre-filter the board (roadmap phases
      // deep-link here with ?milestone=). URL is the only home for filter
      // state; localStorage only holds drag intent. Same post-hydration
      // idiom as the overlay above.
      if (!compact) {
        try {
          const params = new URLSearchParams(window.location.search)
          // `?q=` is the expression, verbatim. The four parameters that
          // shipped before it fold in as terms, so the roadmap's
          // `?milestone=0.3` deep links keep working untouched — and only
          // those four, because reading every field name as a parameter
          // would let an unrelated `?id=42` from a newsletter filter this
          // board to nothing.
          const parts: string[] = []
          const text = params.get("q")
          if (text) {
            parts.push(text)
          }
          for (const name of LEGACY_PARAMS) {
            const values = params.getAll(name).filter(Boolean)
            if (values.length > 0) {
              parts.push(`${name}:${values.map(quoteValue).join(",")}`)
            }
          }
          if (parts.length > 0) {
            // Seeded, not applied: a reader who followed a deep link and
            // has done nothing yet should not be read a filter
            // announcement they did not ask for. The URL is left exactly
            // as it arrived, hash and unrelated parameters included; it is
            // rewritten on the first edit, not on arrival.
            const restored = parts.join(" ")
            setQuery(restored)
            signatureRef.current = restored
          }
        } catch {
          // No URL access (unlikely): render unfiltered.
        }
        // ?card= and ?artifact= restore a reading position: the dialog
        // opens and the drawer opens inside it. Both must resolve to
        // something the drawer can show — a stale link opens nothing
        // rather than a dead drawer — and the URL is left exactly as it
        // arrived, the filter's own rule.
        try {
          const params = new URLSearchParams(window.location.search)
          const cardParam = params.get("card")
          const artifactParam = params.get("artifact")
          if (cardParam && artifactParam) {
            const owner = baseline
              .flatMap((column) => column.cards)
              .find((entry) => entry.uid === cardParam)
            const artifact = (owner?.artifacts ?? []).find(
              (entry) => entry.target === artifactParam
            )
            if (owner && artifact && readerMode(artifact)) {
              setSelectedUid(owner.uid)
              setRestoredArtifact(artifactParam)
            }
          }
        } catch {
          // No URL access: nothing to restore.
        }
      }
      setInteractive(true)
    })
    return () => cancelAnimationFrame(frame)
  }, [storageKey, baseline, compact])

  // One expression, applied on every keystroke and written to the URL, so
  // every filtered view is a shareable deep link. There is no second store
  // of committed facets: the string is the filter.
  const urlTimer = useRef<number | null>(null)
  useEffect(
    () => () => {
      if (urlTimer.current !== null) {
        window.clearTimeout(urlTimer.current)
      }
    },
    []
  )
  const writeQueryUrl = useCallback((trimmed: string) => {
    try {
      // Built from the current location, so a link carrying a fragment
      // or someone else's parameters keeps them. Only the filter
      // parameters are ours to remove.
      const url = new URL(window.location.href)
      for (const name of [...LEGACY_PARAMS, "q"]) {
        url.searchParams.delete(name)
      }
      if (trimmed) {
        url.searchParams.set("q", trimmed)
      }
      window.history.replaceState(
        null,
        "",
        `${url.pathname}${url.search}${url.hash}`
      )
    } catch {
      // History unavailable: the in-memory state still applies.
    }
  }, [])

  const applyQuery = useCallback(
    (next: string) => {
      setQuery(next)
      const trimmed = next.trim()
      // Announce on what the query *means*, not on every keystroke: typing
      // `tag:spec` is eight changes and one filter. The signature skips the
      // states the parser drops, so a half-typed field never announces.
      const terms = parseQuery(trimmed)
      const signature = terms
        .map(
          (term) =>
            `${term.negate ? "-" : ""}${term.field?.key ?? ""}:${term.alternatives
              .map(
                (alternative) => `${alternative.op ?? ""}${alternative.text}`
              )
              .join(",")}`
        )
        .join(" ")
      if (signature !== signatureRef.current) {
        signatureRef.current = signature
        const total = board.reduce(
          (sum, column) => sum + column.cards.length,
          0
        )
        announceSettled(
          terms.length > 0
            ? `${countMatches(board, terms)} of ${total} cards match the filter.`
            : "Filter cleared."
        )
      }
      // The URL only needs to be right when someone can copy it. Safari
      // budgets replaceState (~100 calls per rolling 30s) and the catch
      // below is silent, so a per-keystroke write could quietly stop
      // tracking the query mid-session — the shareable-link contract
      // breaking with no symptom. Settled once per pause, it never gets
      // near the budget. The same settle beat the announcement uses.
      if (urlTimer.current !== null) {
        window.clearTimeout(urlTimer.current)
      }
      urlTimer.current = window.setTimeout(() => {
        urlTimer.current = null
        writeQueryUrl(trimmed)
      }, 600)
    },
    [board, announceSettled, writeQueryUrl]
  )

  const persist = useCallback(
    (next: BoardColumn[]) => {
      setBoard(next)
      const overlay = overlayOf(baseline, next)
      const staged = Object.keys(overlay).length
      setStagedCount(staged)
      try {
        if (staged > 0) {
          window.localStorage.setItem(storageKey, JSON.stringify(overlay))
        } else {
          window.localStorage.removeItem(storageKey)
        }
      } catch {
        // Storage full/unavailable: the in-memory board still works.
      }
    },
    [storageKey, baseline]
  )

  const moveCard = useCallback(
    (uid: string, targetColumn: number) => {
      if (targetColumn < 0 || targetColumn >= board.length) {
        return
      }
      const next = cloneBoard(board)
      let card: IdentifiedCard | undefined
      let sourceColumn = -1
      for (let index = 0; index < next.length; index++) {
        const at = next[index].cards.findIndex((entry) => entry.uid === uid)
        if (at >= 0) {
          if (index === targetColumn) {
            return
          }
          card = next[index].cards.splice(at, 1)[0]
          sourceColumn = index
          break
        }
      }
      if (!card || sourceColumn < 0) {
        return
      }
      next[targetColumn].cards.push(card)
      persist(next)
      announce(
        `Moved "${card.title}" to ${next[targetColumn].title}. That column now holds ${next[targetColumn].cards.length} cards.`
      )
    },
    [board, persist, announce]
  )

  const openDetail = useCallback((uid: string) => {
    setSelectedUid(uid)
  }, [])

  const closeDetail = useCallback(() => {
    setSelectedUid(null)
    // Reopening the same card by hand starts without the drawer: the
    // deep link was honored once, when it arrived.
    setRestoredArtifact(null)
  }, [])

  const handleDragStart = useCallback((uid: string, event: React.DragEvent) => {
    dragRef.current = uid
    setDragUid(uid)
    event.dataTransfer.effectAllowed = "move"
    // Firefox requires data for a drag to start, and the payload stays
    // empty on purpose: a card released over the filter field would
    // otherwise have its id typed into the query.
    event.dataTransfer.setData("text/plain", "")
  }, [])

  const handleDragEnd = useCallback(() => {
    dragRef.current = null
    setDragUid(null)
    setDropTarget(null)
  }, [])

  const handleDrop = useCallback(
    (targetColumn: number) => {
      const uid = dragRef.current
      if (uid) {
        moveCard(uid, targetColumn)
      }
      handleDragEnd()
    },
    [moveCard, handleDragEnd]
  )

  const reset = useCallback(() => {
    try {
      window.localStorage.removeItem(storageKey)
    } catch {
      // Nothing to clear.
    }
    setBoard(baseline)
    setStagedCount(0)
    announce("Board reset to the committed state.")
  }, [storageKey, baseline, announce])

  const exportBoard = useCallback(async () => {
    const exported = boardToMoveCommands(baseline, board)
    try {
      await navigator.clipboard.writeText(exported)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      // Copied is delivered: the download below is the fallback, not a
      // sibling — both at once dropped an unasked-for file next to a
      // clipboard that already had the answer.
      return
    } catch {
      // Clipboard unavailable: fall through to the download.
    }
    const blob = new Blob([exported], {
      type: "text/x-shellscript",
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = "board-moves.sh"
    anchor.click()
    URL.revokeObjectURL(url)
  }, [baseline, board])

  // "/" focuses the filter field, the way every board-shaped tool does
  // it. It is bound only while the board itself holds focus: a
  // single-character shortcut that swallows "/" for the whole page would
  // fail WCAG 2.1.4, and folio ships this component into other people's
  // sites.
  useEffect(() => {
    if (compact) {
      return
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "/" || selectedUid !== null) {
        return
      }
      const active = document.activeElement
      // Inside the board, or nowhere yet. A freshly loaded page leaves
      // focus on <body>, which is exactly when you press `/` — and the
      // badge in the field advertised a shortcut that did nothing until you
      // had clicked something first. `body` still means "no other control
      // has claimed this key", which is what WCAG 2.1.4 is protecting:
      // embedded miniatures return above without binding at all, and a
      // press while typing anywhere is ignored below.
      const owned =
        active === document.body ||
        active === null ||
        sectionRef.current?.contains(active)
      if (!owned) {
        return
      }
      const typing =
        active instanceof HTMLElement &&
        (active.tagName === "INPUT" ||
          active.tagName === "TEXTAREA" ||
          active.isContentEditable)
      if (typing) {
        return
      }
      event.preventDefault()
      searchRef.current?.focus()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [compact, selectedUid])

  // Memoized: FilterPanel keys its count cache on this exact terms
  // reference, and a stable reference per query is what makes an
  // unrelated re-render free there.
  const queryTerms = useMemo(() => parseQuery(query), [query])
  const filtering = queryTerms.length > 0

  // Above the empty-board return below, with every other hook: a hook
  // after an early return is a rules-of-hooks landmine the moment the
  // column set can change across renders of a mounted instance.
  // The rail dismisses in two registers. Escape closes from anywhere, and
  // hands focus back to the toggle when it was inside the rail. A press
  // outside closes only the narrow drawer — on a wide screen the rail is
  // furniture, not a menu: you click the board WHILE filtering.
  useEffect(() => {
    if (!panelOpen || selectedUid !== null) {
      return
    }
    const shut = (returnFocus: boolean) => {
      setPanelOpen(false)
      if (returnFocus) {
        filterToggleRef.current?.focus()
      }
    }
    const onPointer = (event: MouseEvent) => {
      if (window.matchMedia("(min-width: 64rem)").matches) {
        return
      }
      const target = event.target as Node
      if (
        !railRef.current?.contains(target) &&
        !syntaxRef.current?.contains(target)
      ) {
        shut(false)
      }
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented) {
        // An open widget below (the combobox panel) already consumed this
        // key — both listeners share `document`, so this is the belt that
        // holds even if immediate propagation was not stopped.
        return
      }
      if (event.key === "Escape") {
        shut(Boolean(railRef.current?.contains(document.activeElement)))
      }
    }
    document.addEventListener("mousedown", onPointer)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onPointer)
      document.removeEventListener("keydown", onKey)
    }
  }, [panelOpen, selectedUid])
  const visibleBoard = useMemo(
    () =>
      filtering
        ? board.map((column) => ({
            ...column,
            cards: column.cards.filter((card) =>
              matchesQuery(queryTerms, card, column.id, column.title)
            ),
          }))
        : board,
    [board, filtering, queryTerms]
  )

  /* Column widths are view state, not board data: fr weights per column,
     equal until a divider is dragged, held only in memory — the one store
     this board writes is the repository. Key the weights to the live column
     set so stale widths disappear during render without a reset effect. */
  const columnLayoutKey = visibleBoard.map((column) => column.id).join("\u001f")
  const [storedColumnWeights, setStoredColumnWeights] = useState<{
    key: string
    values: number[]
  } | null>(null)
  const columnWeights =
    storedColumnWeights?.key === columnLayoutKey
      ? storedColumnWeights.values
      : null
  const setColumnWeights = (
    next: number[] | null | ((current: number[] | null) => number[] | null)
  ) => {
    setStoredColumnWeights((current) => {
      const currentValues =
        current?.key === columnLayoutKey ? current.values : null
      const values = typeof next === "function" ? next(currentValues) : next
      return values === null ? null : { key: columnLayoutKey, values }
    })
  }
  const boardGridRef = useRef<HTMLDivElement | null>(null)

  if (baseline.length === 0) {
    return (
      <section className="not-prose rounded-lg border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          No kanban columns configured.
        </p>
      </section>
    )
  }

  // Cards are addressed by uid, so a filtered view is as safe to move
  // from as an unfiltered one — the drag machinery never reads a position.
  // Every column empty, with a filter on. Said once, above the grid,
  // instead of once per column: four identical lines is not four facts.
  const nothingMatches =
    filtering && visibleBoard.every((column) => column.cards.length === 0)

  /* One grid track per column, so a five-column board reads left to right
     instead of wrapping a second row. The 13rem floor is what hands a too
     narrow canvas to the workspace x-scroll rather than crushing tracks. */
  const columnTracks = (columnWeights ?? visibleBoard.map(() => 1))
    .map((weight) => `minmax(13rem, ${weight}fr)`)
    .join(" ")

  const resizeFloor = 0.35

  const beginColumnResize = (
    event: React.PointerEvent<HTMLDivElement>,
    index: number
  ) => {
    const grid = boardGridRef.current
    if (!grid) return
    event.preventDefault()
    const startX = event.clientX
    const weights = columnWeights ?? visibleBoard.map(() => 1)
    const pair = weights[index] + weights[index + 1]
    const sections = Array.from(grid.children) as HTMLElement[]
    if (!sections[index] || !sections[index + 1]) return
    // px per fr from the two live tracks, so the drag follows the pointer
    // 1:1 whatever the current distribution is.
    const pxPerFr =
      (sections[index].offsetWidth + sections[index + 1].offsetWidth) / pair
    const onMove = (move: PointerEvent) => {
      const deltaFr = (move.clientX - startX) / pxPerFr
      const next = [...weights]
      next[index] = Math.min(
        Math.max(weights[index] + deltaFr, resizeFloor),
        pair - resizeFloor
      )
      next[index + 1] = pair - next[index]
      setColumnWeights(next)
    }
    const onUp = () => {
      window.removeEventListener("pointermove", onMove)
      window.removeEventListener("pointerup", onUp)
    }
    window.addEventListener("pointermove", onMove)
    window.addEventListener("pointerup", onUp)
  }

  const nudgeColumnResize = (
    event: React.KeyboardEvent<HTMLDivElement>,
    index: number
  ) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return
    event.preventDefault()
    setColumnWeights((current) => {
      const weights = current ?? visibleBoard.map(() => 1)
      const pair = weights[index] + weights[index + 1]
      const step = event.key === "ArrowRight" ? 0.1 : -0.1
      const next = [...weights]
      next[index] = Math.min(
        Math.max(weights[index] + step, resizeFloor),
        pair - resizeFloor
      )
      next[index + 1] = pair - next[index]
      return next
    })
  }

  const selectedColumn = selectedUid
    ? board.findIndex((column) =>
        column.cards.some((card) => card.uid === selectedUid)
      )
    : -1
  const selectedCard =
    selectedColumn >= 0
      ? (board[selectedColumn].cards.find((card) => card.uid === selectedUid) ??
        null)
      : null
  const draggingColumn = dragUid
    ? board.findIndex((column) =>
        column.cards.some((card) => card.uid === dragUid)
      )
    : -1

  /* Local only, as a card.

     It was a band of loose prose with a rule under it, which is how the
     landing separates sections — but this is not a section, it is one
     object saying one thing, sitting on a surface made of objects. Text
     with no edges between the navbar and the toolbar had nothing to belong
     to. So it takes the board's own card: 1px border, 8px radius, on
     --card, with the eyebrow the cards use.

     It reads in the same order a card does — eyebrow, then the line that
     matters, then one line of detail — because the thing above the board
     should be built like the things in it.

     The first draft spent forty words explaining static hosting to someone
     who had just dragged a card and wanted to know what happened to it.
     The eyebrow is the mode, the bold line is the state, and the last line
     is export-then-apply. */
  const stagingCard =
    !compact && interactive && dirty ? (
      <div
        data-slot="kanban-staging"
        className="mb-5 flex flex-wrap items-start justify-between gap-x-8 gap-y-4 rounded-lg border border-border bg-card px-5 py-4"
      >
        <div className="min-w-0 flex-1">
          <span className="block font-mono text-[11px] leading-4 tracking-[0.14em] text-warning uppercase">
            Local only
          </span>
          <p className="m-0 mt-1.5 text-base leading-6 font-semibold text-foreground">
            Nothing you change here is applied
          </p>
          <p className="m-0 mt-1 text-sm leading-6 text-muted-foreground">
            {stagedCount === 1
              ? "1 move staged in this browser. Export it, then apply it in a clone."
              : `${stagedCount} moves staged in this browser. Export them, then apply them in a clone.`}
          </p>
        </div>
        {/* Two, stacked, filling the card.

            Revert and export are the only two things you can do about a
            staged move — undo was a third button for a weaker version of
            revert. Side by side at 32px they sat against three lines of
            text with the card's height unused below them; in a column they
            take that height, which makes them the size of the decision
            they are. */}
        <span className="flex shrink-0 flex-col items-stretch gap-2 self-stretch sm:w-44">
          <button
            type="button"
            onClick={exportBoard}
            className="flex flex-1 items-center justify-center rounded-md border border-primary bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            {copied ? "Copied" : "Export moves"}
          </button>
          <button
            type="button"
            onClick={reset}
            className="flex flex-1 items-center justify-center rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:border-muted-foreground hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            Reset to source
          </button>
        </span>
      </div>
    ) : null

  return (
    <section
      ref={sectionRef}
      data-slot="kanban"
      /* Workspace mode: the section is exactly the viewport below the
         fixed navbar, and nothing inside it adds to the page's scroll
         height — the canvas scrolls instead. Everything is lg-gated: below
         lg the page flows and the rail is the same drawer as everywhere. */
      className={cn(
        "not-prose",
        workspace && "lg:h-[calc(100dvh-var(--nextra-navbar-height,0px))]"
      )}
      aria-label={title || "Kanban board"}
      aria-describedby={description ? descriptionId : undefined}
    >
      {/* The configured description says what the board is to someone
          arriving from elsewhere. On a working surface it does not earn a
          paragraph, so it stays as the board's accessible description —
          read by screen readers, carried into the Markdown mirror, out of
          the way of the columns. */}
      {description ? (
        <p id={descriptionId} className="sr-only">
          {description}
        </p>
      ) : null}

      <p
        key={announcement.seq}
        className="sr-only"
        role="status"
        aria-live="polite"
      >
        {announcement.text}
      </p>

      {/* Everything the open card sits on top of. A modal has to take the
          page with it: focus was already trapped, but a screen reader's
          virtual cursor walks the document rather than the tab ring, so
          every card behind the overlay stayed readable. CardDetail is a
          sibling of this wrapper, not a child, so it stays live. */}
      <div
        inert={selectedUid !== null && !compact ? true : undefined}
        className={workspace ? "lg:h-full" : undefined}
      >
        {/* The masthead. This is the site's own opening — the landing
            sets an eyebrow in mono, tracked, uppercase, in the accent,
            then a sentence-case headline under it — pointed at the board
            instead of at a marketing section. The board used to open with
            a 14px label because height was the scarce resource; it is
            still scarce, and this costs 177px once, at the top, never
            repeated. What paid for it was the card: dropping the
            description the popup already carries took cards from 167px to
            114px, so the board shows more work after the masthead than it
            did without one.

            The toolbar hangs off the headline on the same band, the way
            the landing hangs "Explore the docs" off a section title, so
            the controls cost no row of their own. It no longer sticks:
            a masthead that follows you down the page is a banner. */}
        {/* The staging card sits above the whole surface — except in
            workspace mode, where the rail runs the workspace's full height
            and nothing above the row may push it down, so the card renders
            inside the board column instead (see below). One JSX value, two
            slots, only ever one of them live. */}
        {!workspace ? stagingCard : null}

        {/* A compact board is embedded at a width nobody can predict — a
            docs page, a landing panel, someone else's MDX — so it lays out
            against its container, not the viewport. With viewport
            breakpoints a 600px embed on a 1440px screen still asked for
            three tracks and wrapped a four-column board onto two rows,
            cropping the last column. The full board owns its page, where
            container and viewport agree, so it keeps the plain breakpoints
            and the toolbar budget measured against them.

            In workspace mode this is the workspace itself: a flex row the
            full height of the section — the rail a full-height panel on
            the left, the board column beside it — replacing the in-flow
            grid the docs embed keeps. The section is full-bleed, so no
            flex gap: the rail's right border is the divider, and the
            board column carries its own padding. */}
        <div
          className={
            workspace
              ? "lg:flex lg:h-full lg:min-h-0 lg:gap-0"
              : !compact && interactive && panelOpen
                ? "lg:grid lg:grid-cols-[17rem_minmax(0,1fr)] lg:gap-5"
                : undefined
          }
        >
          {!compact && interactive ? (
            <FilterPanel
              id={`${instanceId}-filter-rail`}
              board={board}
              terms={queryTerms}
              query={query}
              open={panelOpen}
              workspace={workspace}
              railRef={railRef}
              onChange={applyQuery}
            />
          ) : null}
          {/* The board column. In workspace mode it is a flex column with
              one growing child — the canvas — so the staging card, the bar
              and the diagnosis keep their height and the columns scroll in
              what is left. `lg:pt-5` is the daylight under the navbar the
              layout's frame padding used to provide; `lg:px-6` is the side
              padding it used to provide — 24px off the rail's border on
              the left, 24px off the viewport on the right, the same air
              whether the rail is open or closed. */}
          <div
            className={cn(
              "min-w-0",
              workspace &&
                "lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:px-6 lg:pt-5"
            )}
          >
            {workspace ? stagingCard : null}
            {/* `!compact` alone, not `!compact && interactive`: the bar is
                part of the static page. `interactive` is false during SSR
                and the first client frame, so gating on it would strip the
                bar — and the sr-only h1 inside it, the page's only h1 —
                from the export, and pop it in at hydration. */}
            {!compact ? (
              <div data-slot="kanban-filters" className="mb-5">
                {/* The heading is for the document outline, not for the page.
                    A masthead reading "Work board" over "Folio Development
                    Board" spent 88px above the first card to say twice what
                    the navbar, the URL and the four columns already say. The
                    h1 stays so the page still has one, and costs nothing. */}
                {title ? <h1 className="sr-only">{title}</h1> : null}

                {/* The field takes the row, and the controls sit at its end.

                    The card count that used to share this row is gone: it
                    sat above four column headers already printing 22, 0/3,
                    4/3 and 0, and when a filter narrowed the board those four
                    narrowed with it — a total that answered a question the
                    page had already answered four times. */}
                <div className="flex flex-wrap items-center gap-2">
                  <div
                    ref={syntaxRef}
                    className="relative flex min-h-8 min-w-0 flex-1 flex-wrap items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-ring"
                  >
                    {/* The mark at the head of the field is the control. It
                        used to be decoration, with an identical mark at the
                        other end that opened the composer — two filter icons
                        in one field, one of them inert. */}
                    <button
                      type="button"
                      ref={filterToggleRef}
                      onClick={() => setPanelOpen((open) => !open)}
                      aria-expanded={panelOpen}
                      aria-controls={
                        panelOpen ? `${instanceId}-filter-rail` : undefined
                      }
                      aria-label="Filter by field"
                      className={cn(
                        "-ml-1 flex size-6 shrink-0 items-center justify-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                        panelOpen
                          ? "bg-muted text-foreground"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                    >
                      <FilterGlyph className="size-3.5" />
                    </button>
                    <input
                      ref={searchRef}
                      type="text"
                      value={query}
                      onChange={(event) => applyQuery(event.target.value)}
                      /* Two placeholders, because one cannot be both. The
                         long one teaches the language in the space a desktop
                         toolbar has; on a phone the field is ~130px and that
                         string truncated mid-token to "Filter — status:in-r",
                         which teaches a syntax error. The short one fits and
                         still shows the shape; the control at the end of the
                         field holds the rest, and `aria-describedby` reads
                         them out. */
                      placeholder={
                        narrowToolbar
                          ? "Filter — tag:spec"
                          : "Filter — status:in-review tag:spec,launch -priority:high"
                      }
                      aria-label="Filter cards by expression"
                      aria-describedby={`${instanceId}-syntax`}
                      onKeyDown={(event) => {
                        if (event.key !== "Escape") {
                          return
                        }
                        // Escape clears the expression rather than reaching
                        // the card dialog behind the board.
                        event.stopPropagation()
                        if (query) {
                          applyQuery("")
                        }
                      }}
                      spellCheck={false}
                      autoComplete="off"
                      autoCapitalize="off"
                      autoCorrect="off"
                      className="min-w-16 flex-1 border-0 bg-transparent py-0.5 font-mono text-xs text-foreground placeholder:font-sans placeholder:text-muted-foreground focus:outline-none"
                    />
                    {/* Clearing, at every width. It used to be a "Clear"
                        button beside the field that was `hidden` below `sm`,
                        so on a phone a filtered board could not be unfiltered
                        except by selecting the text. */}
                    {query ? (
                      <button
                        type="button"
                        onClick={() => {
                          applyQuery("")
                          searchRef.current?.focus()
                        }}
                        aria-label="Clear the filter"
                        className="flex size-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                      >
                        <CloseGlyph className="size-3" />
                      </button>
                    ) : null}
                    {/* The hint advertises a keyboard shortcut, so it goes
                        where the bar is too tight to spend 24px on one. */}
                    <kbd className="hidden rounded border border-border bg-background px-1.5 font-mono text-xs leading-4 text-muted-foreground sm:inline-block">
                      /
                    </kbd>
                    <SyntaxRules id={`${instanceId}-syntax`} />
                  </div>
                </div>
              </div>
            ) : null}

            {nothingMatches && !compact ? (
              <FilterDiagnosis board={board} terms={queryTerms} />
            ) : null}
            {/* The canvas. In workspace mode it is the one child of the
                board column that grows, and the only thing on the page
                that scrolls — both axes, so a narrow window pans the
                columns instead of crushing them. */}
            <div
              className={
                cn(
                  compact && "@container",
                  workspace && "lg:min-h-0 lg:flex-1 lg:overflow-auto"
                ) || undefined
              }
            >
              <div
                data-slot="kanban-board"
                ref={boardGridRef}
                className={cn(
                  "grid",
                  compact
                    ? "gap-2 @lg:grid-cols-2 @2xl:grid-cols-3 @3xl:grid-cols-4"
                    : workspace
                      ? /* Every column in one row from lg up — the tracks
                           variable carries one weighted slot per column,
                           so a five-column board never wraps downward. */
                        "gap-3 sm:grid-cols-2 lg:[grid-template-columns:var(--kanban-tracks)]"
                      : "gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
                  workspace && "lg:min-w-[48rem]"
                )}
                style={
                  workspace && !compact
                    ? ({
                        "--kanban-tracks": columnTracks,
                      } as React.CSSProperties)
                    : undefined
                }
              >
                {visibleBoard.map((column, columnIndex) => (
                  <section
                    key={column.id}
                    data-slot="kanban-column"
                    data-column={column.id}
                    aria-labelledby={`kanban-${column.id}`}
                    onDragOver={(event) => {
                      if (dragRef.current) {
                        event.preventDefault()
                        event.dataTransfer.dropEffect = "move"
                        setDropTarget(columnIndex)
                      }
                    }}
                    onDragLeave={(event) => {
                      /* Moving from the column's own padding onto its header
                     or card list fires dragleave too — the old
                     target===currentTarget check read that as an exit and
                     churned the highlight set→clear→set per crossing.
                     Only a leave whose destination is outside the column
                     clears it. */
                      if (
                        !event.currentTarget.contains(
                          event.relatedTarget as Node | null
                        )
                      ) {
                        setDropTarget((current) =>
                          current === columnIndex ? null : current
                        )
                      }
                    }}
                    onDrop={(event) => {
                      event.preventDefault()
                      handleDrop(columnIndex)
                    }}
                    /* No lane fill and no lane border at rest. The landing
                 separates its content with rules and space rather than
                 containers, and a filled trough around a column of bordered
                 cards is a box inside a box. A column reads from its header
                 and the gap beside it; it only takes a surface while a card
                 is dragged over it, which is the one moment the column
                 itself is the target. */
                    className={cn(
                      "relative min-w-0 rounded-lg border transition-colors",
                      compact ? "p-1.5" : "p-2",
                      dropTarget === columnIndex &&
                        draggingColumn !== columnIndex
                        ? "border-primary/40 bg-primary/[0.03]"
                        : "border-transparent"
                    )}
                  >
                    {/* The divider lives in the gap to this column's right.
                        Dragging it trades width with the neighbor, a double
                        click restores the even split, and arrow keys do the
                        same trade for a keyboard. */}
                    {workspace && columnIndex < visibleBoard.length - 1 ? (
                      <div
                        role="separator"
                        aria-orientation="vertical"
                        aria-label={`Resize the ${column.title} column`}
                        tabIndex={0}
                        onPointerDown={(event) =>
                          beginColumnResize(event, columnIndex)
                        }
                        onDoubleClick={() => setColumnWeights(null)}
                        onKeyDown={(event) =>
                          nudgeColumnResize(event, columnIndex)
                        }
                        className="absolute inset-y-2 -right-2.5 hidden w-1.5 cursor-col-resize rounded-full transition-colors hover:bg-border focus-visible:bg-border focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring lg:block"
                      />
                    ) : null}
                    <div
                      data-slot="kanban-column-header"
                      /* Flush with the cards, and ruled off from them. The
                     header carried 6px of its own inset, so every column
                     label sat 6px to the right of the column it named; now
                     the label, the rule and the card edges are one line.
                     The rule is what makes four stacks read as four
                     columns without giving each one a trough to sit in. */
                      className={cn(
                        "flex items-center gap-2 border-b border-border",
                        compact ? "pt-1 pb-1.5" : "pt-1.5 pb-2"
                      )}
                    >
                      {/* A column name is structure, not a heading competing with
                  the board's own h1: one label register for both variants,
                  which is what leaves the h1 as the only sentence-case
                  foreground string on the surface. `truncate` holds the
                  header to one line at every column width, so its height
                  never depends on how long a column is called.

                  `aria-label` is not redundant. An accessible name is
                  computed from *rendered* text, so `uppercase` really does
                  turn "In progress" into "IN PROGRESS" in the a11y tree —
                  for this heading and for the column region that points at
                  it — and some screen readers spell short all-caps tokens
                  out letter by letter. The label pins the spoken name to
                  the authored one. */}
                      {compact ? (
                        <p
                          id={`kanban-${column.id}`}
                          aria-label={column.title}
                          className="m-0 truncate font-mono text-[11px] leading-4 tracking-[0.14em] text-primary uppercase"
                        >
                          {column.title}
                        </p>
                      ) : (
                        <h2
                          id={`kanban-${column.id}`}
                          aria-label={column.title}
                          className="m-0 truncate font-mono text-[11px] leading-4 tracking-[0.14em] text-primary uppercase"
                        >
                          {column.title}
                        </h2>
                      )}
                      <span className="ml-auto">
                        <WipBadge
                          count={column.cards.length}
                          limit={filtering ? null : column.limit}
                        />
                      </span>
                    </div>

                    {/* `role="list"` wraps the cards and nothing else. A list may
                only contain list items, so the "+N more" line and the
                empty-column placeholder used to be dropped outright by the
                tools that enforce that — the empty state was invisible to
                a screen reader while the column announced itself as a list
                of zero things, with no explanation. They are siblings of
                the list now, and read as ordinary text in the column. */}
                    <div
                      data-slot="kanban-card-list"
                      className={cn(
                        "m-0 grid list-none gap-2 p-0",
                        compact ? "pt-2" : "pt-2.5"
                      )}
                    >
                      {column.cards.length > 0 ? (
                        <>
                          <div role="list" className="grid gap-2">
                            {(maxCardsPerColumn !== undefined
                              ? column.cards.slice(
                                  0,
                                  Math.max(maxCardsPerColumn, 0)
                                )
                              : column.cards
                            ).map((card) => (
                              <BoardCard
                                key={card.uid}
                                card={card}
                                interactive={interactive}
                                compact={compact}
                                dragging={dragUid === card.uid}
                                onDragStart={handleDragStart}
                                onDragEnd={handleDragEnd}
                                onOpen={openDetail}
                              />
                            ))}
                          </div>
                          {maxCardsPerColumn !== undefined &&
                          column.cards.length > maxCardsPerColumn ? (
                            <p className="m-0 pt-0.5 font-mono text-[11px] leading-4 tracking-[0.14em] text-muted-foreground uppercase">
                              +{column.cards.length - maxCardsPerColumn} more
                            </p>
                          ) : null}
                        </>
                      ) : nothingMatches ? null : (
                        /* An empty column is empty. It used to be a dashed box
                       the size of a card — the only dashed thing on a
                       surface built from hairlines, and the loudest object
                       in the quietest column. The rule above already says
                       where the column is; this only has to say why nothing
                       is under it.

                       Nothing at all when the whole board is empty: the
                       reading above already said so once, and each header
                       still prints its own 0. Four columns repeating one
                       sentence is not four facts. */
                        <p
                          className={cn(
                            "m-0 text-xs text-muted-foreground",
                            compact ? "pt-0.5" : "pt-1"
                          )}
                        >
                          {filtering
                            ? "No cards match."
                            : dragUid
                              ? "Drop cards here."
                              : "No cards in this column."}
                        </p>
                      )}

                      {/* The drop lands at the end of the column, so the placeholder
                  sits there too: the gap you see is the slot you get. */}
                      {dropTarget === columnIndex &&
                      draggingColumn !== columnIndex ? (
                        <div
                          aria-hidden="true"
                          className="h-9 rounded-md border border-dashed border-primary/50 bg-primary/[0.06]"
                        />
                      ) : null}
                    </div>
                  </section>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {!compact && selectedCard ? (
        <CardDetail
          card={selectedCard}
          columns={board}
          columnIndex={selectedColumn}
          canMove={interactive}
          canAttach={interactive}
          roadmapHref={roadmapHref}
          /* The one line `Export moves` will write for this card, or empty
             when it still sits where the repository put it. Built from the
             same `committedColumns` baseline and the same `column.id` that
             `boardToMoveCommands` uses, so the footer cannot drift from the
             export. */
          moveCommand={
            committedColumns(baseline).get(selectedCard.uid) !==
              board[selectedColumn].id && selectedCard.id
              ? `folio kanban move ${selectedCard.id} ${board[selectedColumn].id}`
              : ""
          }
          onMove={(target) => moveCard(selectedCard.uid, target)}
          onClose={closeDetail}
          initialArtifact={restoredArtifact}
        />
      ) : null}
    </section>
  )
}
