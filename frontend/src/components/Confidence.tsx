function confidenceLabel(value: number) {
  if (value >= 0.85) return { label: 'alta', guidance: 'mantenha a revisão antes de confirmar' }
  if (value >= 0.6) return { label: 'média', guidance: 'revise evidências e justificativas' }
  return { label: 'baixa', guidance: 'revisão manual necessária' }
}

export function Confidence({ value }: { value?: number }) {
  if (value == null) return <span className="confidence">Confiança não informada — revisão manual necessária</span>
  const normalized = value > 1 ? value / 100 : value
  const { label, guidance } = confidenceLabel(normalized)
  return <span className={`confidence confidence--${label}`}>Confiança {Math.round(normalized * 100)}% ({label}) — {guidance}</span>
}
