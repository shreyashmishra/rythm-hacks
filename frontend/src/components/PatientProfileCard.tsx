import type { PatientProfile } from '../types/ehr'
import { formatAge, formatDate, formatLabel, formatList } from '../lib/formatters'

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-slate-50 p-4">
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-medium leading-6 text-ink">{value}</p>
    </div>
  )
}

export function PatientProfileCard({
  profile,
  title = 'Patient profile',
  subtitle = 'Core patient record details',
}: {
  profile: PatientProfile
  title?: string
  subtitle?: string
}) {
  return (
    <section className="rounded-[28px] border border-line bg-white p-6">
      <div className="flex flex-col gap-3 border-b border-line pb-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent">{subtitle}</p>
          <h2 className="mt-3 text-2xl font-semibold text-ink">{title}</h2>
          <p className="mt-2 text-sm text-slate-500">{profile.fullName}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
          Visible profile summary card
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ProfileField label="DOB" value={formatDate(profile.dateOfBirth)} />
        <ProfileField label="Age" value={formatAge(profile.age)} />
        <ProfileField label="Sex" value={formatLabel(profile.sex)} />
        <ProfileField
          label="Emergency contact"
          value={`${formatLabel(profile.emergencyContactName)} / ${formatLabel(profile.emergencyContactPhone)}`}
        />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <ProfileField label="Allergies" value={formatList(profile.allergies)} />
        <ProfileField
          label="Chronic conditions"
          value={formatList(profile.chronicConditions)}
        />
        <ProfileField label="Medications" value={formatList(profile.medications)} />
      </div>
    </section>
  )
}
