"use client"

import { cn } from "@/lib/utils"
import { useMemo } from "react"

interface FileTreeProps {
  tree: string
}

interface TreeNode {
  name: string
  isFolder: boolean
  children: TreeNode[]
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={cn("size-4 shrink-0", className)}
    >
      <path d="M3.75 3A1.75 1.75 0 0 0 2 4.75v3.26a3.235 3.235 0 0 1 1.75-.51h12.5c.644 0 1.245.188 1.75.51V6.75A1.75 1.75 0 0 0 16.25 5h-4.836a.25.25 0 0 1-.177-.073L9.823 3.513A1.75 1.75 0 0 0 8.586 3H3.75Z" />
      <path d="M3.75 9A1.75 1.75 0 0 0 2 10.75v4.5c0 .966.784 1.75 1.75 1.75h12.5A1.75 1.75 0 0 0 18 15.25v-4.5A1.75 1.75 0 0 0 16.25 9H3.75Z" />
    </svg>
  )
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={cn("size-4 shrink-0", className)}
    >
      <path d="M3 3.5A1.5 1.5 0 0 1 4.5 2h6.879a1.5 1.5 0 0 1 1.06.44l4.122 4.12A1.5 1.5 0 0 1 17 7.622V16.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 16.5v-13Z" />
    </svg>
  )
}

function parseTree(tree: string): TreeNode[] {
  const lines = tree.split("\n").filter((line) => line.trim().length > 0)
  if (lines.length === 0) return []

  // Detect indentation unit from the first indented line
  let indentUnit = 2
  for (const line of lines) {
    const match = line.match(/^(\s+)/)
    if (match) {
      indentUnit = match[1].length
      break
    }
  }

  const root: TreeNode[] = []
  const stack: { node: TreeNode; depth: number }[] = []

  for (const line of lines) {
    const match = line.match(/^(\s*)(.+)$/)
    if (!match) continue

    const indent = match[1].length
    const depth = indent === 0 ? 0 : Math.round(indent / indentUnit)
    const rawName = match[2].trim()
    const isFolder = rawName.endsWith("/")
    const name = isFolder ? rawName.slice(0, -1) : rawName

    const node: TreeNode = { name, isFolder, children: [] }

    if (depth === 0) {
      root.push(node)
      stack.length = 0
      stack.push({ node, depth: 0 })
    } else {
      // Pop stack until we find the parent
      while (stack.length > 0 && stack[stack.length - 1].depth >= depth) {
        stack.pop()
      }
      if (stack.length > 0) {
        stack[stack.length - 1].node.children.push(node)
      } else {
        root.push(node)
      }
      stack.push({ node, depth })
    }
  }

  return root
}

function TreeNodeRow({
  node,
  isLast,
  prefix,
}: {
  node: TreeNode
  isLast: boolean
  prefix: string
}) {
  const connector = isLast ? "└── " : "├── "
  const childPrefix = prefix + (isLast ? "    " : "│   ")

  return (
    <>
      <div className="flex items-center leading-7 whitespace-pre">
        <span className="text-muted-foreground/50 select-none">{prefix}{connector}</span>
        {node.isFolder ? (
          <FolderIcon className="text-primary/70 mr-1.5" />
        ) : (
          <FileIcon className="text-muted-foreground/60 mr-1.5" />
        )}
        <span
          className={cn(
            node.isFolder ? "text-foreground font-medium" : "text-foreground/80"
          )}
        >
          {node.name}
        </span>
      </div>
      {node.children.map((child, i) => (
        <TreeNodeRow
          key={`${child.name}-${i}`}
          node={child}
          isLast={i === node.children.length - 1}
          prefix={childPrefix}
        />
      ))}
    </>
  )
}

function RootNode({ node }: { node: TreeNode }) {
  return (
    <>
      <div className="flex items-center leading-7 whitespace-pre">
        {node.isFolder ? (
          <FolderIcon className="text-primary/70 mr-1.5" />
        ) : (
          <FileIcon className="text-muted-foreground/60 mr-1.5" />
        )}
        <span
          className={cn(
            node.isFolder ? "text-foreground font-medium" : "text-foreground/80"
          )}
        >
          {node.name}
        </span>
      </div>
      {node.children.map((child, i) => (
        <TreeNodeRow
          key={`${child.name}-${i}`}
          node={child}
          isLast={i === node.children.length - 1}
          prefix=""
        />
      ))}
    </>
  )
}

export function FileTree({ tree }: FileTreeProps) {
  const nodes = useMemo(() => parseTree(tree), [tree])

  if (nodes.length === 0) return null

  return (
    <div
      className={cn(
        "my-5 rounded-lg border border-border bg-muted/30 px-4 py-3",
        "font-mono text-sm overflow-x-auto"
      )}
    >
      {nodes.map((node, i) => (
        <RootNode key={`${node.name}-${i}`} node={node} />
      ))}
    </div>
  )
}
