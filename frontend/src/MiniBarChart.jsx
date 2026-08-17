const numberFormat = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export default function MiniBarChart({ title, labels, values }) {
  if (!labels?.length || !values?.length) return null

  const max = Math.max(...values.map((v) => Math.abs(v)), 1)

  return (
    <div className="mini-chart" role="img" aria-label={title || 'Chart'}>
      {title && <div className="mini-chart-title">{title}</div>}
      <div className="mini-chart-bars">
        {labels.map((label, i) => {
          const value = values[i]
          const pct = Math.max((Math.abs(value) / max) * 100, 3)
          return (
            <div className="mini-chart-row" key={`${label}-${i}`}>
              <span className="mini-chart-label" title={label}>
                {label}
              </span>
              <div className="mini-chart-track">
                <div className="mini-chart-bar" style={{ width: `${pct}%` }} />
              </div>
              <span className="mini-chart-value">{numberFormat.format(value)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
