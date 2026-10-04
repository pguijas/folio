import type { ComponentProps, FC } from "react"
import { Pre, withIcons } from "nextra/components"

type PreProps = ComponentProps<typeof Pre>

// Languages that carry no highlighting, so a preset names no language for them.
const PLAIN_LANGUAGES = new Set(["plaintext", "text", "txt"])

// Nextra's code block reads data-language for its icon and drops it. The copy
// under data-lang reaches the <pre>, where a preset can name the language. A
// block with a filename also gets the language as a label in its header, after
// the icon; the label is hidden unless a preset shows it.
function LanguagePre({ icon, ...props }: PreProps) {
  const language = props["data-language"]
  const label = language && !PLAIN_LANGUAGES.has(language) ? language : undefined
  return (
    <Pre
      {...props}
      data-lang={language}
      icon={
        <>
          {icon}
          {label && <span data-slot="code-block-language">{label}</span>}
        </>
      }
    />
  )
}

export const CodeBlockPre = withIcons(LanguagePre as FC)
