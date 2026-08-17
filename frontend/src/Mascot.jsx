export default function Mascot({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="Procurement AI assistant"
    >
      <defs>
        <linearGradient id="mascot-head" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#3987e5" />
          <stop offset="100%" stopColor="#1c5cab" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#mascot-head)" />
      <line x1="32" y1="6" x2="32" y2="13" stroke="#cde2fb" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="5" r="2.5" fill="#eda100" />
      <g stroke="#0b0b0b" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <rect x="13" y="27" width="15" height="12" rx="4" fill="#fcfcfb" fillOpacity="0.95" />
        <rect x="36" y="27" width="15" height="12" rx="4" fill="#fcfcfb" fillOpacity="0.95" />
        <line x1="28" y1="32" x2="36" y2="32" />
        <line x1="9" y1="30" x2="13" y2="31" />
        <line x1="51" y1="31" x2="55" y2="30" />
      </g>
      <circle cx="19.5" cy="33" r="1.8" fill="#2a78d6" />
      <circle cx="42.5" cy="33" r="1.8" fill="#2a78d6" />
      <path d="M23 46 Q32 51 41 46" stroke="#0b0b0b" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  )
}
