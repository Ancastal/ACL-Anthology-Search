'use client'

import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'
  text?: string
}

export default function LoadingSpinner({ size = 'medium', text }: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6',
    large: 'w-8 h-8'
  }

  const containerClasses = {
    small: 'gap-2',
    medium: 'gap-2',
    large: 'gap-3'
  }

  return (
    <div className={`flex items-center justify-center ${containerClasses[size]}`}>
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      {text && (
        <span className={`text-gray-600 ${
          size === 'large' ? 'text-lg' : size === 'small' ? 'text-sm' : 'text-base'
        }`}>
          {text}
        </span>
      )}
    </div>
  )
}