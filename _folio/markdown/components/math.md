# Math (LaTeX)

Inline and display math rendering via [KaTeX](https://katex.org/). Use `$` for inline expressions and `$$` for centered display equations. Math support is enabled by default — no configuration needed.

## API

Math uses Markdown syntax, not a JSX component:

| Syntax | Behavior | Description |
|--------|----------|-------------|
| `$...$` | Inline | Renders the expression inline with surrounding text. |
| `$$...$$` | Display (block) | Renders the expression as a centered block equation. |

Math expressions inside code blocks (`` ` `` or ` ``` `) are **not** rendered — they display as literal text, so you can safely document LaTeX syntax.

## Example

### Inline math

```md
The Pythagorean theorem states that $a^2 + b^2 = c^2$ for a right triangle.
Einstein's famous equation $E = mc^2$ relates energy and mass.
```

The Pythagorean theorem states that $a^2 + b^2 = c^2$ for a right triangle.
Einstein's famous equation $E = mc^2$ relates energy and mass.

### Display equations

```md
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

### Matrices

```md
$$
\begin{bmatrix} a_{11} & a_{12} \\ a_{21} & a_{22} \end{bmatrix}
\begin{bmatrix} x_1 \\ x_2 \end{bmatrix} =
\begin{bmatrix} b_1 \\ b_2 \end{bmatrix}
$$
```

$$
\begin{bmatrix} a_{11} & a_{12} \\ a_{21} & a_{22} \end{bmatrix}
\begin{bmatrix} x_1 \\ x_2 \end{bmatrix} =
\begin{bmatrix} b_1 \\ b_2 \end{bmatrix}
$$

### Summations

```md
The binomial theorem:

$$
(x + y)^n = \sum_{k=0}^{n} \binom{n}{k} x^{n-k} y^k
$$
```

The binomial theorem:

$$
(x + y)^n = \sum_{k=0}^{n} \binom{n}{k} x^{n-k} y^k
$$
