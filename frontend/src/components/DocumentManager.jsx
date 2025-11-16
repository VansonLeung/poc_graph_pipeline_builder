import { useEffect, useMemo, useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select } from './ui/select'

const getDefaultFormState = () => ({
  content: '',
  metadata: '',
  buildKg: false,
  schemaKey: 'business',
  performEntityResolution: true,
})

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
  const [form, setForm] = useState(() => getDefaultFormState())
  const [editingDoc, setEditingDoc] = useState(null)

  const schemaOptions = useMemo(
    () => [
      { value: 'auto', label: 'Auto-extract schema from this content' },
      { value: 'business', label: 'Business preset' },
      { value: 'academic', label: 'Academic preset' },
      { value: '', label: 'Use builder default' },
    ],
    [],
  )

  useEffect(() => {
    setForm(getDefaultFormState())
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

    if (form.buildKg) {
      metadata.build_kg = true
      if (form.schemaKey) {
        metadata.schema_key = form.schemaKey
      }
      metadata.perform_entity_resolution = form.performEntityResolution
    }

    const payload = { content: form.content, metadata }
    if (editingDoc) {
      onUpdateDocument(selectedIndex, editingDoc.doc_id, payload).then(() => {
        setEditingDoc(null)
        setForm(getDefaultFormState())
      })
    } else {
      onCreateDocument(selectedIndex, payload).then(() => setForm(getDefaultFormState()))
    }
  }

  const handleEdit = (doc) => {
    setEditingDoc(doc)
    const editableMetadata = { ...(doc.metadata || {}) }
    const buildKg = Boolean(editableMetadata.build_kg)
    const schemaKey = editableMetadata.schema_key || 'business'
    const performEntityResolution =
      editableMetadata.perform_entity_resolution ?? form.performEntityResolution
    delete editableMetadata.build_kg
    delete editableMetadata.schema_key
    delete editableMetadata.perform_entity_resolution

    setForm({
      content: doc.content,
      metadata: JSON.stringify(editableMetadata, null, 2),
      buildKg,
      schemaKey,
      performEntityResolution,
    })
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
                <div className="space-y-3 rounded-lg border border-slate-800 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="build-kg" className="text-base">
                        Build knowledge graph from this content
                      </Label>
                      <p className="text-xs text-slate-400">
                        Mirrors the workflows from example_kg_builder.py (schema selection + entity resolution).
                      </p>
                    </div>
                    <input
                      id="build-kg"
                      type="checkbox"
                      className="h-4 w-4"
                      checked={form.buildKg}
                      onChange={(e) => setForm((prev) => ({ ...prev, buildKg: e.target.checked }))}
                    />
                  </div>
                  {form.buildKg ? (
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="schema-select">Schema strategy</Label>
                        <Select
                          id="schema-select"
                          value={form.schemaKey}
                          onChange={(e) => setForm((prev) => ({ ...prev, schemaKey: e.target.value }))}
                        >
                          {schemaOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                        <p className="text-xs text-slate-400">
                          Choose “Auto-extract” to infer a schema from this document before ingesting.
                        </p>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="entity-resolution" className="text-sm">
                            Perform entity resolution
                          </Label>
                          <p className="text-xs text-slate-400">Exact/semantic/fuzzy passes per builder config.</p>
                        </div>
                        <input
                          id="entity-resolution"
                          type="checkbox"
                          className="h-4 w-4"
                          checked={form.performEntityResolution}
                          onChange={(e) =>
                            setForm((prev) => ({ ...prev, performEntityResolution: e.target.checked }))
                          }
                        />
                      </div>
                    </div>
                  ) : null}
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
                    {doc.metadata && Object.keys(doc.metadata || {}).length ? (
                      <pre className="mt-3 whitespace-pre-wrap rounded bg-slate-950/60 p-3 text-xs text-slate-300">
                        {JSON.stringify(doc.metadata, null, 2)}
                      </pre>
                    ) : null}
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
