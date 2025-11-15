import { cn } from '../../lib/utils'

export const Select = ({ className, children, ...props }) => (
  <select
    className={cn(
      'h-10 w-full rounded-md border border-slate-800 bg-slate-900 px-3 text-sm text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
      className,
    )}
    {...props}
  >
    {children}
  </select>
)
