import { LucideIcon, ArrowUp, ArrowDown } from 'lucide-react'
import { Card } from '../ui/Card'
import { cn } from '../../lib/utils'

interface SummaryCardProps {
  label: string
  value: string
  subValue: string
  icon: LucideIcon
  color: string
  bg: string
  isGain?: boolean
  onClick?: () => void
  className?: string
  style?: React.CSSProperties
  // react-grid-layout props (passed down)
  onMouseDown?: React.MouseEventHandler
  onMouseUp?: React.MouseEventHandler
  onTouchEnd?: React.TouchEventHandler
}

export function SummaryCard({
  label,
  value,
  subValue,
  icon: Icon,
  color,
  bg,
  isGain,
  onClick,
  className,
  style,
  onMouseDown,
  onMouseUp,
  onTouchEnd,
  ...props
}: SummaryCardProps) {
  return (
    <Card
      noPadding
      className={cn(
        "relative overflow-hidden transition-all hover:shadow-md flex flex-col justify-between h-full p-4",
        onClick ? "cursor-pointer ring-1 ring-transparent hover:ring-blue-500" : "",
        className
      )}
      onClick={onClick}
      style={style}
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
      onTouchEnd={onTouchEnd}
      {...props}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center gap-3 mb-3">
          <div className={cn('rounded-lg p-2', bg)}>
            <Icon className={cn('h-5 w-5', color)} />
          </div>
          <div className="flex items-baseline gap-1">
            <p className="text-sm font-medium text-gray-900">{label}</p>
            <span className={cn(
              'text-xs flex items-center gap-0.5',
              isGain 
                ? subValue.includes('-') ? 'text-blue-600' : 'text-red-600'
                : 'text-gray-500'
            )}>
              {isGain && (
                subValue.includes('-') ? (
                  <ArrowDown className="h-3 w-3" />
                ) : (
                  <ArrowUp className="h-3 w-3" />
                )
              )}
              <span>({subValue})</span>
            </span>
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-2xl font-bold tracking-tight text-gray-900">
            {value}
          </h3>
        </div>
      </div>
    </Card>
  )
}
