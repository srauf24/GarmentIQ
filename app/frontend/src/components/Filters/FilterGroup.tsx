interface FilterGroupProps {
  label: string;
  options: string[];
  value: string | undefined;
  onChange: (value: string | undefined) => void;
}

export function FilterGroup({
  label,
  options,
  value,
  onChange,
}: FilterGroupProps) {
  if (options.length === 0) return null;

  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-500">
        {label}
      </label>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value || undefined)}
        className="w-full rounded-sm border border-gray-300 bg-white px-2 py-1.5 text-sm
                   focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      >
        <option value="">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
