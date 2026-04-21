export function isPlaceholderGroup(item) {
  const name = String(item?.group_name || '').trim()
  return /^[?？]\s*\+?\s*\d+$/.test(name)
}

export function filterVisibleGroups(items) {
  return (Array.isArray(items) ? items : []).filter((item) => !isPlaceholderGroup(item))
}
