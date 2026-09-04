import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { TypeBadge } from "@/components/type-badge"

interface Param {
  name: string
  type: string
  default?: string
  description: string
  href?: string
}

interface ParamTableProps {
  args: Param[]
}

export function ParamTable({ args }: ParamTableProps) {
  if (args.length === 0) return null

  return (
    <div className="my-4 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[150px]">Name</TableHead>
            <TableHead className="w-[120px]">Type</TableHead>
            <TableHead className="w-[100px]">Default</TableHead>
            <TableHead>Description</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {args.map((arg) => (
            <TableRow key={arg.name}>
              <TableCell className="font-mono font-medium">{arg.name}</TableCell>
              <TableCell>
                <TypeBadge type={arg.type} href={arg.href} />
              </TableCell>
              <TableCell className="font-mono text-muted-foreground">
                {arg.default || "-"}
              </TableCell>
              <TableCell>{arg.description}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
