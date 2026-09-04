import type { ThemePreset } from "./preset-types"

interface PresetGroup {
  id: string
  label: string
  presetIds: string[]
}

const registeredPresets = new Map<string, ThemePreset>()
const registeredGroups = new Map<string, PresetGroup>()

export function registerPreset(preset: ThemePreset, groupId?: string): void {
  const existing = registeredPresets.get(preset.id)
  if (existing && existing !== preset) {
    console.warn(
      `[preset-registry] Preset with id "${preset.id}" already registered. Replacing existing preset.`
    )
  }
  registeredPresets.set(preset.id, preset)

  if (groupId !== undefined) {
    let group = registeredGroups.get(groupId)
    if (!group) {
      // Create a placeholder group so registration order does not matter.
      // A later registerGroup call merges its label and preset ids into it.
      group = { id: groupId, label: groupId, presetIds: [] }
      registeredGroups.set(groupId, group)
    }
    if (!group.presetIds.includes(preset.id)) {
      group.presetIds.push(preset.id)
    }
  }
}

export function registerGroup(
  id: string,
  label: string,
  presetIds: string[]
): void {
  const existing = registeredGroups.get(id)
  if (!existing) {
    registeredGroups.set(id, { id, label, presetIds: [...presetIds] })
    return
  }

  // Merge with a group that registerPreset may have created as a placeholder:
  // adopt the label and union the preset ids.
  existing.label = label
  for (const presetId of presetIds) {
    if (!existing.presetIds.includes(presetId)) {
      existing.presetIds.push(presetId)
    }
  }
}

export function getPresets(): ThemePreset[] {
  return Array.from(registeredPresets.values())
}

export function getGroups(): Array<{ id: string; label: string; presetIds: string[] }> {
  return Array.from(registeredGroups.values())
}

export interface DisplayPresetGroup {
  id: string
  label: string
  presetIds: string[]
  presets: ThemePreset[]
}

// Resolve group memberships into concrete presets for display. Presets are
// deduped across groups (first group wins; presets.ts registers the "project"
// group first, so a project preset that reuses a builtin id only shows under
// Project). Presets that belong to no group render in a fallback "Other"
// group so presets registered through the extension API are never invisible.
// Groups that end up empty are dropped.
export function groupPresetsForDisplay(
  groups: Array<{ id: string; label: string; presetIds: string[] }>,
  allPresets: ThemePreset[]
): DisplayPresetGroup[] {
  const presetsById = new Map(allPresets.map((preset) => [preset.id, preset]))
  const seenPresetIds = new Set<string>()
  const displayGroups: DisplayPresetGroup[] = groups.map((group) => ({
    ...group,
    presets: group.presetIds
      .map((presetId) => presetsById.get(presetId))
      .filter((preset): preset is ThemePreset => {
        if (!preset || seenPresetIds.has(preset.id)) return false
        seenPresetIds.add(preset.id)
        return true
      }),
  }))

  const ungroupedPresets = allPresets.filter(
    (preset) => !seenPresetIds.has(preset.id)
  )
  if (ungroupedPresets.length > 0) {
    displayGroups.push({
      id: "other",
      label: "Other",
      presetIds: ungroupedPresets.map((preset) => preset.id),
      presets: ungroupedPresets,
    })
  }

  return displayGroups.filter((group) => group.presets.length > 0)
}
