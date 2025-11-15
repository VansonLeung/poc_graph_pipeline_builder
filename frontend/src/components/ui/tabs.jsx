import React, { createContext, useContext } from 'react'
import { cn } from '../../lib/utils'

const TabsContext = createContext()

const useTabs = () => {
  const ctx = useContext(TabsContext)
  if (!ctx) {
    throw new Error('Tabs components must be used within <Tabs>')
  }
  return ctx
}

export const Tabs = ({ value, onValueChange, children }) => {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className="space-y-4">{children}</div>
    </TabsContext.Provider>
  )
}

export const TabsList = ({ children }) => (
  <div className="flex gap-2 overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/70 p-1">{children}</div>
)

export const TabsTrigger = ({ value, children }) => {
  const { value: active, onValueChange } = useTabs()
  const isActive = active === value
  return (
    <button
      className={cn(
        'flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors',
        isActive ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-white',
      )}
      onClick={() => onValueChange(value)}
    >
      {children}
    </button>
  )
}

export const TabsContent = ({ value, children }) => {
  const { value: active } = useTabs()
  if (active !== value) {
    return null
  }
  return <div>{children}</div>
}
