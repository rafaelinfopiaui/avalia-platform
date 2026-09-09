import type { ReactNode } from 'react'

export function Alert({ type = 'error', children }: { type?: 'error' | 'info' | 'warning' | 'success'; children: ReactNode }) {
  return <div className={`alert alert--${type}`} role={type === 'error' ? 'alert' : 'status'}>{children}</div>
}
