import { useEffect, useState } from 'react'

const WORD = 'SkillShift AI'

// Plays the green screen + logo, then tells the parent when it's finished.
export default function LoginCurtain({ onDone }: { onDone: () => void }) {
  // 0 = green screen in, 1 = logo pops, 2 = logo slides up, 3 = screen slides up
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const timers = [
      setTimeout(() => setStage(1), 400),
      setTimeout(() => setStage(2), 1700),
      setTimeout(() => setStage(3), 2050),
      setTimeout(onDone, 3100),
    ]
    return () => timers.forEach(clearTimeout)
  }, [onDone])

  return (
    <div className={`lc lc-s${stage}`} aria-hidden="true">
        <span className="lc-blob lc-b1" />
        <span className="lc-blob lc-b2" />
        <div className="lc-logo">
            <span className="lc-spark">✦</span>
            {WORD.split('').map((ch, i) => (
                <span key={i} className={`lc-ch${i >= 11 ? ' lc-ai' : ''}`} style={{ ['--n' as string]: i }}>
                {ch === ' ' ? '\u00a0' : ch}
                </span>
            ))}
        </div>
    </div>
  )
}