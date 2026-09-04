from __future__ import annotations

import gzip
import json
import os
import re
import warnings
from pathlib import Path
from urllib.parse import urlsplit


class StaticAssetRewriter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def fix_asset_paths(self) -> None:
        """Rewrite local URLs so static files work when opened via file://."""
        self._copy_opengraph_images_with_png_extension()
        has_file_search = self._write_file_search_fallback()
        for root, _dirs, files in os.walk(self.output_dir):
            for fname in files:
                if not fname.endswith((".html", ".txt", ".js")):
                    continue
                fpath = Path(root) / fname
                if self._is_next_asset(fpath):
                    self._patch_next_runtime_asset_prefix(fpath)
                    continue
                original = fpath.read_text(encoding="utf-8")
                content = original
                if has_file_search and fname.endswith(".html"):
                    content = self._inject_file_search_script(content)
                content = self._rewrite_opengraph_image_urls(content)
                patched = self.rewrite_file_urls(content, fpath)
                if patched != original:
                    fpath.write_text(patched, encoding="utf-8")

    def _copy_opengraph_images_with_png_extension(self) -> None:
        for path in self.output_dir.rglob("opengraph-image"):
            if not path.is_file() or path.suffix:
                continue
            image = path.read_bytes()
            png_path = path.with_name("opengraph-image.png")
            if not png_path.exists() or png_path.read_bytes() != image:
                png_path.write_bytes(image)

    @staticmethod
    def _rewrite_opengraph_image_urls(content: str) -> str:
        return re.sub(
            r"opengraph-image(?!\.png)(?=(?:[?\"'<\\]|$))",
            "opengraph-image.png",
            content,
        )

    def rewrite_file_urls(self, content: str, fpath: Path) -> str:
        content, script_bodies = self._stash_script_bodies(content)

        attr_pattern = re.compile(
            r"(?P<prefix>(?<![\w:-])(?P<attr>data-href|href|poster|src)=)"
            r"(?P<quote>[\"'])"
            r"(?P<url>[^\"']+)(?P=quote)"
        )
        serialized_pattern = re.compile(
            r"(?P<prefix>\\?\"(?P<attr>data-href|href|poster|src)\\?\":\\?\")"
            r"(?P<url>/[^\"\\]+)(?P<suffix>\\?\")"
        )

        def replace_attr(match: re.Match[str]) -> str:
            url = match.group("url")
            rewritten = self.rewrite_file_url(
                url, fpath, route_index=match.group("attr") == "data-href"
            )
            return f"{match.group('prefix')}{match.group('quote')}{rewritten}{match.group('quote')}"

        def replace_serialized(match: re.Match[str]) -> str:
            url = match.group("url")
            rewritten = self.rewrite_file_url(
                url, fpath, route_index=match.group("attr") == "data-href"
            )
            return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

        content = attr_pattern.sub(replace_attr, content)
        content = serialized_pattern.sub(replace_serialized, content)
        return self._restore_script_bodies(content, script_bodies)

    def rewrite_file_url(
        self, url: str, fpath: Path, *, route_index: bool = False
    ) -> str:
        split = urlsplit(url)
        if (
            split.scheme
            or split.netloc
            or not split.path
            or split.path.startswith("#")
            or url.startswith(
                ("mailto:", "tel:", "javascript:", "data:", "blob:", "//")
            )
        ):
            return url

        root = self.output_dir.resolve()
        current_dir = fpath.parent.resolve()

        if split.path.startswith("/"):
            target_file = self._file_url_target_under_root(
                root / split.path.lstrip("/"), root
            )
        else:
            target_file = self._file_url_target_under_root(
                current_dir / split.path, root
            )
            if (
                target_file is None
                and fpath.name == "index.html"
                and current_dir != root
            ):
                # A page served at /docs/a/b/ is written by a source file that
                # sits one level up (docs/a/b.md), so its author - and the link
                # checker, which resolves source-relative - both read a sibling
                # link like "./c" against /docs/a/. Retry there when output-dir
                # resolution finds nothing, so the links the checker blesses are
                # the links the browser follows. Output-dir resolution keeps
                # precedence: a link that already resolves is left alone.
                target_file = self._file_url_target_under_root(
                    current_dir.parent / split.path, root
                )

        if target_file is None:
            return url

        relative_target = (
            target_file.parent
            if route_index and target_file.name == "index.html"
            else target_file
        )
        relative = os.path.relpath(relative_target, current_dir).replace(os.sep, "/")
        if relative.startswith("_next/"):
            # os.path.relpath never emits a "./" prefix, so pages at the
            # output root would reference chunks as bare "_next/...". The
            # Turbopack runtime prefix shim (below) derives its chunk prefix
            # from the script tag's src attribute; keep every emitted form
            # uniform ("./" or "../") so the prefix and the raw attributes
            # the runtime compares against always agree.
            relative = f"./{relative}"
        if route_index and target_file.name == "index.html":
            relative = "./" if relative == "." else relative.rstrip("/") + "/"
        if split.query:
            relative = f"{relative}?{split.query}"
        if split.fragment:
            relative = f"{relative}#{split.fragment}"
        return relative

    def _is_next_asset(self, fpath: Path) -> bool:
        try:
            relative = fpath.resolve().relative_to(self.output_dir.resolve())
        except ValueError:
            return False
        return bool(relative.parts) and relative.parts[0] == "_next"

    def _patch_next_runtime_asset_prefix(self, fpath: Path) -> None:
        if not fpath.name.startswith("turbopack-") or fpath.suffix != ".js":
            return
        content = fpath.read_text(encoding="utf-8")
        if '"/_next/"' not in content:
            return
        # Use the script tag's src ATTRIBUTE (not the resolved .src property):
        # the runtime identifies already-loaded chunks by comparing prefix
        # against other script tags' attributes, which this rewriter has
        # relativized to the same "../_next/" form. An absolute URL here never
        # matches, and the runtime then waits forever for chunks that are
        # already loaded - hydration stalls with no console error.
        portable_prefix = (
            '(()=>{let e="object"==typeof document&&document.currentScript&&'
            'document.currentScript.getAttribute("src")||"";'
            "let t=e.match(/^((?:.*\\/)?_next\\/)static\\/chunks\\//);"
            'return t?t[1]:"/_next/"})()'
        )
        patched = content.replace('"/_next/"', portable_prefix, 1)
        # The chunk-path builder is a minified function whose NAME and captured
        # prefix/suffix identifiers change between Turbopack releases (seen as
        # N, then q). Match the body shape and preserve whatever identifiers
        # the current runtime uses instead of hardcoding them.
        chunk_path_fn = re.compile(
            r"function (?P<fn>[A-Za-z_$][\w$]*)\(e\)\{return`"
            r"\$\{(?P<pre>[A-Za-z_$][\w$]*)\}"
            r"\$\{(?P<mid>e|e\.split\(\"/\"\)\.map\(e=>encodeURIComponent\(e\)\)\.join\(\"/\"\))\}"
            r"\$\{(?P<suf>[A-Za-z_$][\w$]*)\}`\}"
        )

        def patch_chunk_path_fn(match: re.Match[str]) -> str:
            fn, pre, mid, suf = match.group("fn", "pre", "mid", "suf")
            return (
                f'function {fn}(e){{let _fp=e.indexOf("/_next/");'
                f"_fp>=0&&(e=e.slice(_fp+7));"
                f"return`${{{pre}}}${{{mid}}}${{{suf}}}`}}"
            )

        patched, simple_fn_matches = chunk_path_fn.subn(patch_chunk_path_fn, patched)

        # Next 16.3 keeps the same path builder but gives the prefix a default
        # argument and stores the encoded path in a local variable first:
        # ``function q(e,t=P){let n=K.test(e)?...:e;return`${t}${n}${r}`}``.
        # Pin the full body shape so this cannot accidentally rewrite an
        # unrelated two-argument runtime helper.
        encoded_chunk_path_fn = re.compile(
            r"function (?P<fn>[A-Za-z_$][\w$]*)\("
            r"(?P<path>[A-Za-z_$][\w$]*),"
            r"(?P<pre>[A-Za-z_$][\w$]*)=(?P<default>[A-Za-z_$][\w$]*)\)\{"
            r"let (?P<encoded>[A-Za-z_$][\w$]*)="
            r"(?P<unsafe>[A-Za-z_$][\w$]*)\.test\((?P=path)\)\?"
            r"(?P=path)\.split\(\"/\"\)\.map\(encodeURIComponent\)"
            r"\.join\(\"/\"\):(?P=path);return`"
            r"\$\{(?P=pre)\}\$\{(?P=encoded)\}"
            r"\$\{(?P<suf>[A-Za-z_$][\w$]*)\}`\}"
        )

        def patch_encoded_chunk_path_fn(match: re.Match[str]) -> str:
            path = match.group("path")
            guard = (
                f'let _fp={path}.indexOf("/_next/");'
                f"_fp>=0&&({path}={path}.slice(_fp+7));"
            )
            return match.group(0).replace("{", "{" + guard, 1)

        patched, encoded_fn_matches = encoded_chunk_path_fn.subn(
            patch_encoded_chunk_path_fn, patched
        )
        fn_matches = simple_fn_matches + encoded_fn_matches
        if fn_matches == 0:
            warnings.warn(
                "static_rewriter: Turbopack chunk-path function not found in "
                f"{fpath.name}; the runtime shape may have changed and "
                "hydration of relative-URL exports may break. "
                "Update _patch_next_runtime_asset_prefix for the new runtime.",
                stacklevel=2,
            )
        if patched != content:
            fpath.write_text(patched, encoding="utf-8")

    @staticmethod
    def _stash_script_bodies(content: str) -> tuple[str, list[str]]:
        script_bodies: list[str] = []
        script_pattern = re.compile(
            r"(?P<open><script\b[^>]*>)(?P<body>[\s\S]*?)(?P<close></script>)",
            re.IGNORECASE,
        )

        def stash(match: re.Match[str]) -> str:
            index = len(script_bodies)
            script_bodies.append(match.group("body"))
            return f"{match.group('open')}@@FOLIO_SCRIPT_BODY_{index}@@{match.group('close')}"

        return script_pattern.sub(stash, content), script_bodies

    @staticmethod
    def _restore_script_bodies(content: str, script_bodies: list[str]) -> str:
        for index, body in enumerate(script_bodies):
            content = content.replace(f"@@FOLIO_SCRIPT_BODY_{index}@@", body)
        return content

    def _write_file_search_fallback(self) -> bool:
        fragment_dir = self.output_dir / "_pagefind" / "fragment"
        if not fragment_dir.exists():
            return False

        documents = []
        for fragment_path in sorted(fragment_dir.glob("*.pf_fragment")):
            fragment = self._read_pagefind_fragment(fragment_path)
            if not fragment:
                continue
            url = self._pagefind_file_url(str(fragment.get("url", "")))
            content = str(fragment.get("content", ""))
            meta = (
                fragment.get("meta") if isinstance(fragment.get("meta"), dict) else {}
            )
            title = str(meta.get("title") or content.split(".", 1)[0] or url)
            documents.append(
                {
                    "url": url,
                    "title": title,
                    "content": content,
                }
            )

        if not documents:
            return False

        index_json = json.dumps(documents, ensure_ascii=True, separators=(",", ":"))
        fallback = self._file_search_script(index_json)
        (self.output_dir / "_folio-search.js").write_text(fallback, encoding="utf-8")
        return True

    @staticmethod
    def _read_pagefind_fragment(fragment_path: Path) -> dict | None:
        try:
            payload = gzip.decompress(fragment_path.read_bytes())
        except (OSError, EOFError):
            return None
        json_start = payload.find(b"{")
        if json_start == -1:
            return None
        try:
            parsed = json.loads(payload[json_start:].decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    def _pagefind_file_url(self, url: str) -> str:
        split = urlsplit(url)
        if split.scheme or split.netloc:
            return url

        root = self.output_dir.resolve()
        target_path = (root / split.path.lstrip("/")).resolve()
        target_file = self._file_url_target(target_path)
        if target_file is None:
            path = split.path.lstrip("/")
            if not path:
                path = "index.html"
            elif path.endswith("/"):
                path = f"{path}index.html"
            elif not Path(path).suffix:
                path = f"{path}/index.html"
        else:
            path = os.path.relpath(target_file, root).replace(os.sep, "/")

        if split.query:
            path = f"{path}?{split.query}"
        if split.fragment:
            path = f"{path}#{split.fragment}"
        return path

    @staticmethod
    def _inject_file_search_script(content: str) -> str:
        if "_folio-search.js" in content:
            return content
        script = '<script defer src="/_folio-search.js"></script>'
        if "<head>" in content:
            return content.replace("<head>", f"<head>{script}", 1)
        if "</head>" in content:
            return content.replace("</head>", f"{script}</head>", 1)
        return content

    @staticmethod
    def _file_search_script(index_json: str) -> str:
        return (
            "(function(){\n"
            f"const documents={index_json};\n"
            "let options={};\n"
            "const script=document.currentScript;\n"
            "const rootHref=new URL('./',script&&script.src||document.baseURI).href;\n"
            "function normalize(value){return String(value||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}\n"
            "function escapeHtml(value){return String(value).replace(/[&<>\"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[ch];});}\n"
            "function escapeRegex(value){return String(value).replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');}\n"
            "function splitPath(path){return path.split('/').filter(Boolean);}\n"
            "function currentDir(){const current=new URL(location.href);const root=new URL(rootHref);let rel=decodeURIComponent(current.pathname).slice(decodeURIComponent(root.pathname).length);if(!rel||rel.endsWith('/'))return rel;return rel.split('/').slice(0,-1).join('/')+'/';}\n"
            "function relativePath(target){if(/^(https?:)?\\/\\//.test(target))return target;const hashIndex=target.indexOf('#');const hash=hashIndex>=0?target.slice(hashIndex):'';const noHash=hashIndex>=0?target.slice(0,hashIndex):target;const queryIndex=noHash.indexOf('?');const query=queryIndex>=0?noHash.slice(queryIndex):'';const path=queryIndex>=0?noHash.slice(0,queryIndex):noHash;const from=splitPath(currentDir());const to=splitPath(path);while(from.length&&to.length&&from[0]===to[0]){from.shift();to.shift();}let rel=[...from.map(function(){return '..';}),...to].join('/')||'index.html';if(location.protocol==='file:'&&/\\.html$/.test(rel))rel+='?folio-search=1';return rel+query+hash;}\n"
            "function excerpt(content,terms){const normalized=normalize(content);let index=-1;for(const term of terms){index=normalized.indexOf(term);if(index!==-1)break;}const start=Math.max(0,index-80);const raw=String(content||'').slice(start,start+220).trim();let html=escapeHtml((start>0?'... ':'')+raw+(start+220<String(content||'').length?' ...':''));for(const term of terms){if(!term)continue;html=html.replace(new RegExp('('+escapeRegex(escapeHtml(term))+')','ig'),'<mark>$1</mark>');}return html;}\n"
            "function search(term){const terms=normalize(term).split(/\\s+/).filter(Boolean);if(!terms.length)return [];return documents.map(function(doc){const title=normalize(doc.title);const content=normalize(doc.content);const haystack=title+' '+content;if(!terms.every(function(token){return haystack.includes(token);})){return null;}const titleHits=terms.filter(function(token){return title.includes(token);}).length;const score=titleHits*10+terms.reduce(function(total,token){return total+(content.includes(token)?1:0);},0);const href=relativePath(doc.url);return {id:doc.url,score:score,words:[],data:async function(){return {url:href,meta:{title:doc.title},sub_results:[{title:doc.title,url:href,excerpt:excerpt(doc.content,terms)}]};}};}).filter(Boolean).sort(function(a,b){return b.score-a.score;});}\n"
            "const api={options:async function(nextOptions){options=nextOptions||options;},preload:async function(){return null;},search:async function(term){const results=search(term);return {results:results,unfilteredResultCount:results.length,filters:{},totalFilters:{},timings:{preload:0,search:0,total:0}};},debouncedSearch:async function(term){return api.search(term,options);}};\n"
            "window.__folioStaticSearch=api;\n"
            "if(location.protocol==='file:'&&!window.pagefind){window.pagefind=api;}\n"
            "})();\n"
        )

    def _file_url_target_under_root(self, target_path: Path, root: Path) -> Path | None:
        resolved = target_path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            return None
        return self._file_url_target(resolved)

    @staticmethod
    def _file_url_target(target_path: Path) -> Path | None:
        if target_path.is_dir():
            index_file = target_path / "index.html"
            return index_file if index_file.exists() else None
        if target_path.is_file():
            return target_path

        index_file = target_path / "index.html"
        if index_file.exists():
            return index_file

        if not target_path.suffix:
            html_file = target_path.with_suffix(".html")
            if html_file.exists():
                return html_file

        return None
