import type { Role } from '../types/auth'

const options: Array<{ role: Role; label: string; hint: string }> = [
  { role: 'patient', label: 'Patient', hint: 'Personal access to your dashboard shell.' },
  { role: 'doctor', label: 'Doctor', hint: 'Clinical access to the doctor dashboard shell.' },
]

export function RoleSelector({
  value,
  onChange,
}: {
  value: Role
  onChange: (role: Role) => void
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-slate-700">Role</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option) => {
          const active = value === option.role

          return (
            <button
              key={option.role}
              className={`rounded-2xl border px-4 py-4 text-left transition ${
                active
                  ? 'border-accent bg-accent/5 text-ink'
                  : 'border-line bg-white text-slate-500 hover:border-slate-300'
              }`}
              onClick={() => onChange(option.role)}
              type="button"
            >
              <span className="block text-sm font-semibold">{option.label}</span>
              <span className="mt-1 block text-xs leading-5">{option.hint}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
