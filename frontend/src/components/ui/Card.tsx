import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  noPadding?: boolean
}

export function Card({ className, children, noPadding = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-xl border border-gray-200/60 shadow-sm overflow-hidden',
        'transition-all duration-200 hover:shadow-md hover:border-blue-100',
        !noPadding && 'p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
