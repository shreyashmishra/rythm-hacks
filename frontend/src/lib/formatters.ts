export function formatDate(value: string | null) {
  if (!value) {
    return 'Not provided'
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

export function formatAge(age: number | null) {
  if (age === null) {
    return 'Not provided'
  }

  return `${age} years`
}

export function formatList(values: string[]) {
  if (values.length === 0) {
    return 'None recorded'
  }

  return values.join(', ')
}

export function formatLabel(value: string | null) {
  if (!value || value.trim().length === 0) {
    return 'Not provided'
  }

  return value
}
