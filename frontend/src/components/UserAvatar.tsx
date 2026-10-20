import { useEffect, useState } from 'react'

type Props = {
  name: string
  imageUrl?: string | null
  size?: 'small' | 'medium' | 'large'
  className?: string
}

// Provider metadata is untrusted. Only load HTTPS avatar images; never embed HTML.
export function safeAvatarUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null
  try {
    const url = new URL(value)
    return url.protocol === 'https:' ? url.href : null
  } catch { return null }
}

function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (!words.length) return 'U'
  return (words.length === 1 ? words[0].slice(0, 2) : words.slice(0, 2).map(word => word[0]).join('')).toUpperCase()
}

export default function UserAvatar({ name, imageUrl, size = 'medium', className = '' }: Props) {
  const src = safeAvatarUrl(imageUrl)
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [src])

  return (
    <span className={`user-avatar user-avatar--${size} ${className}`} title={name}>
      {src && !failed
        ? <img src={src} alt={`${name}'s profile picture`} referrerPolicy="no-referrer" onError={() => setFailed(true)} />
        : <span aria-label={`${name}'s default avatar`} role="img">{initials(name)}</span>}
    </span>
  )
}
