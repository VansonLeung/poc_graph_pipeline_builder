import { useEffect, useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import { api } from './lib/api'
import { Button } from './components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { IndexManager } from './components/IndexManager'
import { DocumentManager } from './components/DocumentManager'
import { SearchPanel } from './components/SearchPanel'

const Dashboard = () => {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState('indexes')
  const [indexes, setIndexes] = useState([])
  const [documents, setDocuments] = useState([])
  const [selectedIndex, setSelectedIndex] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [error, setError] = useState('')

  const loadIndexes = async () => {
    try {
      const data = await api.listIndexes()
      setIndexes(data)
      if (!selectedIndex && data.length) {
        setSelectedIndex(data[0].name)
        loadDocuments(data[0].name)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const loadDocuments = async (name) => {
    if (!name) return
    try {
      const docs = await api.listDocuments(name)
      setDocuments(docs)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadIndexes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSelectIndex = (name) => {
    setSelectedIndex(name)
    loadDocuments(name)
  }

  const createIndex = (payload) => api.createIndex(payload).then(loadIndexes)
  const updateIndex = (name, payload) => api.updateIndex(name, payload).then(loadIndexes)
  const deleteIndex = (name) => api.deleteIndex(name).then(() => {
    if (name === selectedIndex) {
      setSelectedIndex('')
      setDocuments([])
    }
    return loadIndexes()
  })

  const createDocument = (name, payload) => api.createDocument(name, payload).then(() => loadDocuments(name))
  const updateDocument = (name, docId, payload) => api.updateDocument(name, docId, payload).then(() => loadDocuments(name))
  const deleteDocument = (name, docId) => api.deleteDocument(name, docId).then(() => loadDocuments(name))

  const runSearch = (payload) => api.search(payload).then(setSearchResults)

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-900 bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-sm text-slate-400">Welcome back</p>
            <h1 className="text-2xl font-semibold">{user.username}</h1>
          </div>
          <Button variant="outline" onClick={logout}>
            Logout
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        {error ? <p className="rounded-md border border-red-900 bg-red-950 px-4 py-2 text-sm text-red-200">{error}</p> : null}
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="indexes">Indexes</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="search">RAG Search</TabsTrigger>
          </TabsList>
          <TabsContent value="indexes">
            <IndexManager indexes={indexes} onCreate={createIndex} onUpdate={updateIndex} onDelete={deleteIndex} />
          </TabsContent>
          <TabsContent value="documents">
            <DocumentManager
              indexes={indexes}
              documents={documents}
              selectedIndex={selectedIndex}
              onSelectIndex={handleSelectIndex}
              onRefreshDocuments={loadDocuments}
              onCreateDocument={createDocument}
              onUpdateDocument={updateDocument}
              onDeleteDocument={deleteDocument}
            />
          </TabsContent>
          <TabsContent value="search">
            <SearchPanel indexes={indexes} onSearch={runSearch} results={searchResults} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

const AppShell = () => {
  const { user, login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [error, setError] = useState('')

  const handleSubmit = async ({ username, password }) => {
    try {
      setError('')
      if (mode === 'login') {
        await login(username, password)
      } else {
        await register(username, password)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  if (!user) {
    return <LoginPage mode={mode} onSubmit={handleSubmit} toggleMode={() => setMode(mode === 'login' ? 'register' : 'login')} error={error} />
  }

  return <Dashboard />
}

const App = () => (
  <AuthProvider>
    <AppShell />
  </AuthProvider>
)

export default App
