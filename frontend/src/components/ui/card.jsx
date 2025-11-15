import { cn } from '../../lib/utils'

export const Card = ({ className, ...props }) => (
  <div className={cn('rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg', className)} {...props} />
)

export const CardHeader = ({ className, ...props }) => (
  <div className={cn('mb-4 flex flex-col space-y-1', className)} {...props} />
)

export const CardTitle = ({ className, ...props }) => (
  <h3 className={cn('text-lg font-semibold text-white', className)} {...props} />
)

export const CardDescription = ({ className, ...props }) => (
  <p className={cn('text-sm text-slate-400', className)} {...props} />
)

export const CardContent = ({ className, ...props }) => (
  <div className={cn('text-sm text-slate-200', className)} {...props} />
)
