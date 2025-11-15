import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Select } from './ui/select'
import { Textarea } from './ui/textarea'

export const SearchPanel = ({ indexes, onSearch, results }) => {
  const [form, setForm] = useState({ index_name: '', query: '', keywords: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!form.index_name) {
      setError('Select an index before searching')
      return
    }
    setLoading(true)
    setError('')
    try {
      const payload = {
        index_name: form.index_name,
        query: form.query,
        keywords: form.keywords
          ? form.keywords
              .split(',')
              .map((kw) => kw.trim())
              .filter(Boolean)
          : undefined,
      }
      await onSearch(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>RAG Search</CardTitle>
          <CardDescription>Hybrid keyword + vector retrieval backed by Neo4j.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="index-select-search">Index</Label>
              <Select
                id="index-select-search"
                value={form.index_name}
                onChange={(e) => setForm((prev) => ({ ...prev, index_name: e.target.value }))}
              >
                <option value="" disabled>
                  Select an index
                </option>
                {indexes.map((index) => (
                  <option key={index.name} value={index.name}>
                    {index.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="query">Question</Label>
              <Input
                id="query"
                value={form.query}
                onChange={(e) => setForm((prev) => ({ ...prev, query: e.target.value }))}
                placeholder="What are the main AI use cases?"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="keywords">Keywords (comma separated)</Label>
              <Input
                id="keywords"
                value={form.keywords}
                onChange={(e) => setForm((prev) => ({ ...prev, keywords: e.target.value }))}
              />
            </div>
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Result</CardTitle>
          <CardDescription>LLM response with supporting chunks.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {results?.answer ? (
            <div>
              <Label>Answer</Label>
              <Textarea readOnly value={results.answer} className="mt-2 bg-slate-900" rows={6} />
            </div>
          ) : (
            <p className="text-sm text-slate-400">Run a search to see the answer.</p>
          )}
          {results?.chunks?.length ? (
            <div className="space-y-3">
              <Label>Supporting Chunks</Label>
              {results.chunks.map((chunk) => (
                <div key={chunk.doc_id} className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-sm text-slate-200">
                  <p className="text-xs text-slate-400">Score: {chunk.score.toFixed(4)}</p>
                  <p className="mt-2 whitespace-pre-line">{chunk.content}</p>
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
