export const formatCurrency = (value, fallback = 'R$ 0,00') => {
  if (value == null) return fallback
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}
