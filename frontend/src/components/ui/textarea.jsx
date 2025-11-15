import { cn } from '../../lib/utils'

export const Textarea = ({ className, ...props }) => {
  return (
    <textarea
      className={cn(
        'flex w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
        className,
      )}
      {...props}
    />
  )
}
