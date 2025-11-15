import { cn } from '../../lib/utils'

export const Label = ({ className, ...props }) => (
  <label className={cn('text-sm font-medium text-slate-200', className)} {...props} />
)
