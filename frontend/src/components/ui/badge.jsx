import { cn } from '../../lib/utils'

export const Badge = ({ className, ...props }) => (
  <span
    className={cn('inline-flex items-center rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-200', className)}
    {...props}
  />
)
