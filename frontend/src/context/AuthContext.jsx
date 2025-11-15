import React, { createContext, useEffect, useMemo, useState } from 'react'
import { getCurrentUser, loginUser, logoutUser, registerUser } from '../lib/auth'

export const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)

  useEffect(() => {
    setUser(getCurrentUser())
  }, [])

  const login = (username, password) => {
    const session = loginUser(username, password)
    setUser(session)
    return session
  }

  const register = (username, password) => {
    registerUser(username, password)
    const session = loginUser(username, password)
    setUser(session)
    return session
  }

  const logout = () => {
    logoutUser()
    setUser(null)
  }

  const value = useMemo(() => ({ user, login, register, logout }), [user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
