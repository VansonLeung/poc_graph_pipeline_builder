const USERS_KEY = 'gp_users'
const SESSION_KEY = 'gp_session'

const readUsers = () => {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY)) || {}
  } catch {
    return {}
  }
}

const writeUsers = (users) => {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export const registerUser = (username, password) => {
  const users = readUsers()
  if (users[username]) {
    throw new Error('Username already exists')
  }
  users[username] = { password }
  writeUsers(users)
}

export const loginUser = (username, password) => {
  const users = readUsers()
  const user = users[username]
  if (!user || user.password !== password) {
    throw new Error('Invalid credentials')
  }
  const session = { username }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  return session
}

export const logoutUser = () => {
  localStorage.removeItem(SESSION_KEY)
}

export const getCurrentUser = () => {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY))
  } catch {
    return null
  }
}
