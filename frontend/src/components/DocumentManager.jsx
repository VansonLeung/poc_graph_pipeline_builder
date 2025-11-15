import { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select } from './ui/select'

export const DocumentManager = ({
  indexes,
  documents,
  selectedIndex,
  onSelectIndex,
  onRefreshDocuments,
  onCreateDocument,
  onUpdateDocument,
  onDeleteDocument,
}) => {
  const [form, setForm] = useState({ content: '', metadata: '' })
  const [editingDoc, setEditingDoc] = useState(null)

  useEffect(() => {
    setForm({ content: '', metadata: '' })
    setEditingDoc(null)
  }, [selectedIndex])

  const handleSubmit = (event) => {
    event.preventDefault()
    let metadata = {}
    if (form.metadata) {
      try {
        metadata = JSON.parse(form.metadata)
      } catch (error) {
        alert('Metadata must be valid JSON')
        return
      }
    }
    const payload = { content: form.content, metadata }
    if (editingDoc) {
      onUpdateDocument(selectedIndex, editingDoc.doc_id, payload).then(() => {
        setEditingDoc(null)
        setForm({ content: '', metadata: '' })
      })
    } else {
      onCreateDocument(selectedIndex, payload).then(() => setForm({ content: '', metadata: '' }))
    }
  }

  const handleEdit = (doc) => {
    setEditingDoc(doc)
    setForm({ content: doc.content, metadata: JSON.stringify(doc.metadata || {}, null, 2) })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Choose Index</CardTitle>
          <CardDescription>Select which index you want to manage documents for.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-end">
          <div className="flex-1 space-y-2">
            <Label htmlFor="index-select">Index</Label>
            <Select id="index-select" value={selectedIndex || ''} onChange={(e) => onSelectIndex(e.target.value)}>
              <option value="" disabled>
                Select an index
              </option>
              {indexes.map((idx) => (
                <option key={idx.name} value={idx.name}>
                  {idx.name}
                </option>
              ))}
            </Select>
          </div>
          <Button type="button" variant="outline" onClick={() => selectedIndex && onRefreshDocuments(selectedIndex)}>
            Refresh
          </Button>
        </CardContent>
      </Card>

      {selectedIndex ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{editingDoc ? 'Edit Document' : 'Add Document'}</CardTitle>
              <CardDescription>{editingDoc ? `Editing ${editingDoc.doc_id}` : `Documents stored in ${selectedIndex}`}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="doc-content">Content</Label>
                  <Textarea
                    id="doc-content"
                    rows={6}
                    value={form.content}
                    onChange={(e) => setForm((prev) => ({ ...prev, content: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="doc-metadata">Metadata (JSON)</Label>
                  <Textarea
                    id="doc-metadata"
                    rows={4}
                    value={form.metadata}
                    placeholder={`{
  "source": "whitepaper.pdf"
}`}
                    onChange={(e) => setForm((prev) => ({ ...prev, metadata: e.target.value }))}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    {editingDoc ? 'Save changes' : 'Add document'}
                  </Button>
                  {editingDoc ? (
                    <Button type="button" variant="ghost" onClick={() => setEditingDoc(null)}>
                      Cancel
                    </Button>
                  ) : null}
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Documents</CardTitle>
              <CardDescription>Latest documents for the selected index.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {documents.length === 0 ? (
                <p className="text-sm text-slate-400">No documents available.</p>
              ) : (
                documents.map((doc) => (
                  <div key={doc.doc_id} className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
                    <p className="font-medium text-slate-100">{doc.doc_id}</p>
                    <p className="mt-2 text-sm text-slate-300 line-clamp-3">{doc.content}</p>
                    <div className="mt-4 flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEdit(doc)}>
                        Edit
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => onDeleteDocument(selectedIndex, doc.doc_id)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <p className="text-sm text-slate-400">Select an index to manage its documents.</p>
      )}
    </div>
  )
}
