import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'

export const IndexManager = ({ indexes, onCreate, onUpdate, onDelete }) => {
  const [form, setForm] = useState({ name: '', description: '', dimension: '' })
  const [editing, setEditing] = useState(null)

  const resetForm = () => {
    setForm({ name: '', description: '', dimension: '' })
    setEditing(null)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const payload = {
      name: form.name,
      description: form.description || undefined,
      dimension: form.dimension ? Number(form.dimension) : undefined,
    }
    if (editing) {
      onUpdate(editing.name, payload).then(resetForm)
    } else {
      onCreate(payload).then(resetForm)
    }
  }

  const handleEdit = (index) => {
    setEditing(index)
    setForm({
      name: index.name,
      description: index.description || '',
      dimension: index.dimension || '',
    })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{editing ? 'Edit Index' : 'Create Index'}</CardTitle>
          <CardDescription>
            {editing ? `Updating ${editing.name}` : 'Organize documents into isolated semantic indexes'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                disabled={Boolean(editing)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={form.description}
                onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dimension">Vector dimension</Label>
              <Input
                id="dimension"
                type="number"
                value={form.dimension}
                onChange={(e) => setForm((prev) => ({ ...prev, dimension: e.target.value }))}
                placeholder="Defaults to global setting"
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" className="flex-1">
                {editing ? 'Save changes' : 'Create index'}
              </Button>
              {editing ? (
                <Button type="button" variant="ghost" onClick={resetForm}>
                  Cancel
                </Button>
              ) : null}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing Indexes</CardTitle>
          <CardDescription>Click an entry to edit or remove it</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {indexes.length === 0 ? (
            <p className="text-sm text-slate-400">No indexes created yet.</p>
          ) : (
            indexes.map((index) => (
              <div key={index.name} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                <div>
                  <p className="font-medium text-white">{index.name}</p>
                  <p className="text-sm text-slate-400">{index.description || 'No description'}</p>
                  <Badge className="mt-2">{index.dimension || 'default'} dims</Badge>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleEdit(index)}>
                    Edit
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => onDelete(index.name)}>
                    Delete
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}
