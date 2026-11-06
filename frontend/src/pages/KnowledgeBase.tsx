import { useEffect, useState, useRef } from "react"
import { Upload, FileText, Trash2, Loader2 } from "lucide-react"
import { documentsApi } from "../services/api"
import type { Document } from "../types"

export default function KnowledgeBase() {
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = async () => {
    try {
      const res = await documentsApi.list()
      setDocs(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("title", file.name)
      await documentsApi.upload(formData)
      await load()
    } catch (err) {
      console.error(err)
      alert("Upload failed")
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ""
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document?")) return
    try {
      await documentsApi.delete(id)
      setDocs(docs.filter((d) => d.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
          <p className="mt-1 text-sm text-slate-400">Upload company documents for AI retrieval</p>
        </div>
        <div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt,.md,.csv"
            onChange={handleUpload}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className={`inline-flex cursor-pointer items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition ${
              uploading ? "opacity-60 pointer-events-none" : ""
            }`}
          >
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload Document
          </label>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50">
        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          </div>
        ) : docs.length === 0 ? (
          <div className="py-16 text-center">
            <FileText className="mx-auto h-10 w-10 text-slate-600" />
            <p className="mt-3 text-sm text-slate-500">No documents uploaded yet</p>
            <p className="mt-1 text-xs text-slate-600">PDF, DOCX, TXT, MD, CSV supported</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {docs.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-slate-800 p-2">
                    <FileText className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-200">{doc.title}</p>
                    <p className="text-xs text-slate-500">
                      {doc.file_type} · {(doc.file_size / 1024).toFixed(1)} KB · {doc.status}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="rounded-lg p-2 text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
