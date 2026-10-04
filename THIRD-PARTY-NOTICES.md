# Third-Party Notices

Folio is licensed under the MIT License (see [LICENSE](LICENSE)). The following
third-party materials are bundled with Folio or adapted into its source, and
remain governed by their own licenses and terms. Dependencies fetched by Cargo
or pnpm carry their own licenses and are not listed here.

## shadcn/ui

The components under `template/components/ui/` are derived from
[shadcn/ui](https://ui.shadcn.com) registry output and are used under the MIT
License:

```
MIT License

Copyright (c) 2023 shadcn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## docstring_parser

The Google, NumPy, ReST and epydoc docstring parsers in
`crates/folio-ir/src/docstring/` (`google.rs`, `numpy.rs`, `rest.rs` and
`epydoc.rs`) are Rust ports of the matching modules of
[docstring_parser](https://github.com/rr-/docstring_parser) and are used under
the MIT License:

```
The MIT License (MIT)

Copyright (c) 2018 Marcin Kurczewski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## CPython

Two files are derived from [CPython](https://github.com/python/cpython) 3.12
and are used under the Python Software Foundation License Version 2:

- `crates/folio-lang-python/src/unparse.rs`, from the `ast._Unparser` class in
  `Lib/ast.py`;
- `crates/folio-ir/src/docstring/cleandoc.rs`, from `inspect.cleandoc` in
  `Lib/inspect.py`.

Changes made: both are translated to Rust. `unparse.rs` covers expressions
only and renders them from the syntax tree of the ruff Python parser instead of
Python's `ast` nodes. `cleandoc.rs` applies the same normalisation to a Rust
string.

```
PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation;
All Rights Reserved" are retained in Python alone or in any derivative version
prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.
```

## Omarchy

Thanks to the Omarchy project for the palettes and the gallery idea. The 22
palettes in `template/theme/omarchy-palettes.ts` are adapted from the
`themes/*/colors.toml` files of [omacom/omarchy](https://github.com/omacom/omarchy)
and are used under the MIT License. The palette names are Omarchy's, kept so
readers recognise each palette; they imply no endorsement by the owners of
any work or product a name refers to.

The theme picker in `template/components/theme-gallery.tsx` takes the idea of
a gallery of theme slides from [omarchy.org](https://omarchy.org/manual/). Its
code, shapes, sizes, colours and motion are Folio's own, as are the Omarchy
preset's navbar, chapter-list styles and pixel-field background. Its decorative
wordmark reuses Folio's CLI banner. No code, artwork, fonts or style values from
the omarchy.org site are included.

```
Copyright (c) David Heinemeier Hansson

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## cojeev and ui-layouts

The mobile docs drawer, the motion scale, Pastel's layout and component
styles, and the Kbd, Marker and Term components adapt code and values from
[cojeev](https://github.com/luv-jeri/cojeev-ui), used under the MIT License.
cojeev's drawer is adapted from the
[ui-layouts](https://www.ui-layouts.com/components/motion-drawer) motion
drawer, also MIT. Folio Pastel's five palettes, decorative masks, navigation
marker and irregular artwork are Folio's own. Pastel FeatureCard keeps
named Hugeicons over four original organic backgrounds. Component icons
retain Folio's existing icon system. The following layout,
measurements, timings and CSS adaptations retain their upstream attribution:

| Folio | Source | Taken as |
| --- | --- | --- |
| `--folio-motion-micro`, `-element`, `-max` in `template/app/globals.css` | cojeev `registry/cojeev/styles/tokens.css` | values: 120, 200 and 300 ms |
| `--folio-motion-exit`, `--folio-ease-enter`, `--folio-ease-exit` | cojeev `registry/cojeev/motion/choreography.ts` | values: the 180 ms exit and the enter and exit curves |
| `--folio-spring-drawer`, `--folio-motion-drawer` | cojeev `registry/cojeev/ui/motion-drawer.tsx`, from ui-layouts | values: the 180/26/1 spring, sampled as a CSS `linear()` over 560 ms |
| `--folio-drawer-inset`, `-width`, `-radius` | cojeev `app/docs/docs.css` and `components/docs-shell.tsx` | values: 12 px inset, 340 px width (written 21.25rem), radius 24 |
| `--folio-drawer-shadow` | cojeev `registry/cojeev/styles/motion-drawer.css`, from ui-layouts | value: the panel shadow |
| `--folio-drawer-scrim` | cojeev `registry/cojeev/styles/motion-drawer.css` | value: a 30 % scrim |
| `.folio-drawer-title` and `.folio-drawer-close` in `template/app/globals.css` | cojeev `registry/cojeev/styles/motion-drawer.css` | values: the 600 20px/1.3 title at -0.02em, the 44 px round transparent button, its icon's 90° turn on hover, the 2 px focus outline at a 2 px offset |
| the title, close button and scrim in `template/components/mobile-nav-drawer.tsx` | cojeev `registry/cojeev/ui/motion-drawer.tsx` | the idea, re-expressed in Folio's code |
| the Grotesque typography in `template/components/theme-configurator.tsx` and `template/app/layout.tsx` | cojeev `registry/cojeev/styles/theme.css` | the pairing of Bricolage Grotesque for display and DM Sans for text; the fonts come from Google Fonts under the SIL Open Font License, not from cojeev |
| the Pastel sidebar rail and drawer rows in `template/app/styles/shell.css` | cojeev `app/docs/docs.css` | values: the 288 px floating rail, 12 px inset, radius 24, integrated branding and search, 40 px rows and 44 px rows in the drawer |
| the Pastel reading trail in `template/app/styles/shell.css` | cojeev `registry/cojeev/styles/reading-trail.css` and `ui/reading-trail.tsx` | the spine and progress-pill layout; the marker, its anchor positioning and the scroll-driven fill are Folio's own |
| the title-artwork composition in `template/components/pastel-artwork.tsx` and `template/app/styles/pastel-artwork.css` | cojeev `registry/cojeev/ui/shape-artwork.tsx` and `components/docs-atmosphere.tsx` | the arrangement beside the title and the drift and pointer-follow behaviour; the irregular paths and native animation code are Folio's own |
| the Pastel pigment wash in `template/app/styles/shell.css` | cojeev `registry/cojeev/styles/pigment-field.css` | values: the three radial gradients, their positions and strengths |
| `template/app/styles/callout.css` | cojeev `registry/cojeev/styles/alert.css`, `ui/alert.tsx` and `styles/tokens.css` | values: the fill strengths, radius, padding and type, the 40 px icon holder and the corner mark's placement |
| `template/app/styles/disclosure.css` | cojeev `registry/cojeev/styles/tabs.css`, `accordion.css` and `flow-press.css` | values: the 32 px pills, the travelling selected surface, the radius-18 accordion cards 8 px apart with a 60 px trigger; `TabGlide` in `template/components/tabs.tsx` is Folio's own code |
| `template/app/styles/code.css` | cojeev `registry/cojeev/styles/code-block.css` and `styles/tokens.css` | values: the paper-sheet and header layout, language pill, 13 px code at 1.8, five syntax roles in each scheme, and terminal-window layout; the three stationery tabs and `template/components/code-block.tsx` on Nextra's `Pre` are Folio's own |
| `template/app/styles/shapes.css` | cojeev `app/docs/docs.css`, `registry/cojeev/styles/stepper.css`, `milestone-path.css` and `styles/tree.css` | values: the 36 by 42 step tabs and their connector, timeline-marker dimensions and halo, and the file tree's 28 px tiles and ruled elbows; the organic outlines, markup and hooks in `steps.tsx` and `file-tree.tsx` are Folio's own |
| `template/app/styles/surfaces.css` | cojeev `registry/cojeev/styles/card.css`, `badge.css`, `preview.css`, `pattern-background.css`, `empty.css`, `table.css`, `ui/badge.tsx` and `ui/table.tsx` | values: the cards, badges, preview frames and their dot grid, empty states and tables |
| the Pastel block in `template/app/styles/components.css` | cojeev `registry/cojeev/ui/kbd.tsx`, `ui/marker.tsx`, `ui/tooltip.tsx` and `styles/tokens.css` | values: the keycap, dashed divider and definition-card layout with its 120 ms fade |
| the light and dark reveal in `template/lib/scheme-transition.ts` and `template/app/styles/shell.css` | cojeev `registry/cojeev/motion/theme-transition.ts` and `styles/theme-toggle.css` | the idea, a view transition that reveals the new scheme from the control, re-expressed as a plain circle in Folio's code |
| the open and close delays in `template/components/term.tsx` | cojeev `registry/cojeev/ui/hover-card.tsx` | values: 300 and 150 ms; the component is Folio's own, on Radix HoverCard |

```
MIT License

Copyright (c) 2026 Sanjay Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```
MIT License

Copyright (c) 2024 UI LAYOUT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Bricolage Grotesque and DM Sans

The Grotesque typography, the Pastel preset's default, sets headings in
[Bricolage Grotesque](https://github.com/ateliertriay/bricolage) and body text
in [DM Sans](https://github.com/googlefonts/dm-fonts). A site build downloads
both from Google Fonts and serves the files with the site. Both are used under
the SIL Open Font License 1.1:

```
Copyright 2022 The Bricolage Grotesque Project Authors (https://github.com/ateliertriay/bricolage)
Copyright 2014 The DM Sans Project Authors (https://github.com/googlefonts/dm-fonts)

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
https://scripts.sil.org/OFL


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded,
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.
```

## Logos and marks

These marks are trademarks of their respective owners. They are used
referentially, to identify the linked service or the language a page
documents, and are **excluded from Folio's MIT license grant**. Remove or
replace them if your use does not follow the respective owner's brand
guidelines.

- `template/public/icons/chatgpt.svg`: the ChatGPT mark, a trademark of
  OpenAI, used in the "open in assistant" action on generated pages.
- The `RUST_MARK` path in `template/components/landing/sections.tsx`: the Rust
  logo, a trademark of the Rust Foundation. The path data is traced from
  [Simple Icons](https://simpleicons.org), published under CC0 1.0.
