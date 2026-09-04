"use client";

/**
 * RedirectPage preserves published /kanban/ addresses when the board moves.
 *
 * Published instructions (agents.md, board/SKILL.md) teach /kanban/?q= as the
 * report link. When the board is configured to live at a different path, this
 * redirect view at /kanban forwards visitors — query and hash intact — so
 * every published instruction stays true.
 */

import { useEffect } from "react";

export function RedirectPage({ to }: { to: string }) {
  useEffect(() => {
    window.location.replace(to + window.location.search + window.location.hash);
  }, [to]);

  return (
    <div className="prose">
      <p>
        Redirecting to <a href={to}>the board</a>...
      </p>
    </div>
  );
}
