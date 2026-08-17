import { useEffect, useState } from 'react'
import './Splash.css'
import Mascot from './Mascot'

const WELCOME_TEXT = 'Welcome! Ready to explore your procurement data…'
const TYPE_INTERVAL_MS = 35
const WELCOME_AT_MS = 1500
const EXIT_AT_MS = 3500
const FINISH_AT_MS = 4000

const PARTICLES = Array.from({ length: 14 }, (_, i) => ({
  id: i,
  left: (i * 37) % 100,
  top: (i * 53) % 100,
  size: 4 + ((i * 7) % 10),
  delay: (i % 7) * 0.4,
  duration: 5 + (i % 5),
}))

export default function Splash({ onFinish }) {
  const [step, setStep] = useState('logo')
  const [typed, setTyped] = useState('')

  useEffect(() => {
    const toWelcome = setTimeout(() => setStep('welcome'), WELCOME_AT_MS)
    const toExit = setTimeout(() => setStep('exit'), EXIT_AT_MS)
    const finish = setTimeout(() => onFinish(), FINISH_AT_MS)
    return () => {
      clearTimeout(toWelcome)
      clearTimeout(toExit)
      clearTimeout(finish)
    }
  }, [onFinish])

  useEffect(() => {
    if (step === 'logo') return undefined
    let i = 0
    const interval = setInterval(() => {
      i += 1
      setTyped(WELCOME_TEXT.slice(0, i))
      if (i >= WELCOME_TEXT.length) clearInterval(interval)
    }, TYPE_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [step])

  return (
    <div className={`splash ${step === 'exit' ? 'splash-exit' : ''}`}>
      <div className="splash-particles" aria-hidden="true">
        {PARTICLES.map((p) => (
          <span
            key={p.id}
            className="splash-particle"
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              width: p.size,
              height: p.size,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
            }}
          />
        ))}
      </div>
      <div className="splash-card">
        <div className="splash-logo-glow">
          <Mascot size={56} />
        </div>
        <h1 className="splash-title">Procurement AI Assistant</h1>
        <p className="splash-welcome">
          {step !== 'logo' && (
            <>
              {typed}
              <span className="splash-caret" />
            </>
          )}
        </p>
      </div>
    </div>
  )
}
