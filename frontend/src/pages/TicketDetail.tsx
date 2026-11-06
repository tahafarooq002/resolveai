import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Bot, Check, X, Edit3, Loader2, Sparkles } from "lucide-react"
import { ticketsApi, aiApi, approvalsApi } from "../services/api"
import type { Ticket, GeneratedResponse } from "../types"

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editedContent, setEditedContent] = useState("")
  const [actionLoading, setActionLoading] = useState(false)

  const load = async () => {
    if (!id) return
    try {
      const res = await ticketsApi.get(id)
      setTicket(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const handleProcess = async () => {
    if (!id) return
    setProcessing(true)
    try {
      await aiApi.processTicket(id)
      await load()
    } catch (err) {
      console.error(err)
    } finally {
      setProcessing(false)
    }
  }

  const handleApproval = async (action: "approve" | "reject" | "edit", responseId: string) => {
    if (!id) return
    setActionLoading(true)
    try {
      const data: any = { action }
      if (action === "edit") data.edited_content = editedContent
      await approvalsApi.action(id, responseId, data)
      setEditMode(false)
      await load()
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  if (!ticket) return <p className="text-slate-400">Ticket not found</p>

  const latestResponse: GeneratedResponse | undefined = ticket.generated_responses?.[0]
  const customerMessage = ticket.messages?.find((m) => m.role === "customer")

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/tickets" className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-white">{ticket.subject || "Ticket Detail"}</h1>
          <p className="text-sm text-slate-400">
            {ticket.customer_name} · {ticket.customer_email}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left - Messages */}
        <div className="lg:col-span-2 space-y-4">
          {/* Customer Message */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-400">
              Customer Message
            </div>
            <p className="whitespace-pre-wrap text-slate-200 leading-relaxed">
              {customerMessage?.content || "No message"}
            </p>
          </div>

          {/* AI Response */}
          {latestResponse ? (
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-5">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium text-indigo-300">
                  <Bot className="h-4 w-4" /> AI Generated Response
                  <span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                    latestResponse.confidence === "high"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : latestResponse.confidence === "medium"
                      ? "bg-amber-500/20 text-amber-400"
                      : "bg-rose-500/20 text-rose-400"
                  }`}>
                    {latestResponse.confidence} confidence
                  </span>
                </div>
                <span className="text-xs text-slate-500">{latestResponse.status}</span>
              </div>

              {editMode ? (
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  rows={8}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 p-3 text-sm text-white outline-none focus:border-indigo-500"
                />
              ) : (
                <p className="whitespace-pre-wrap text-slate-200 leading-relaxed">
                  {latestResponse.edited_content || latestResponse.content}
                </p>
              )}

              {latestResponse.status === "pending" && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    onClick={() => handleApproval("approve", latestResponse.id)}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    <Check className="h-4 w-4" /> Approve
                  </button>
                  <button
                    onClick={() => {
                      setEditMode(true)
                      setEditedContent(latestResponse.content)
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-600"
                  >
                    <Edit3 className="h-4 w-4" /> Edit
                  </button>
                  {editMode && (
                    <button
                      onClick={() => handleApproval("edit", latestResponse.id)}
                      disabled={actionLoading}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
                    >
                      Save & Approve
                    </button>
                  )}
                  <button
                    onClick={() => handleApproval("reject", latestResponse.id)}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600/80 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-500 disabled:opacity-50"
                  >
                    <X className="h-4 w-4" /> Reject
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/30 p-8 text-center">
              <Sparkles className="mx-auto h-8 w-8 text-slate-500" />
              <p className="mt-3 text-sm text-slate-400">No AI response yet</p>
              <button
                onClick={handleProcess}
                disabled={processing}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
                Process with AI
              </button>
            </div>
          )}
        </div>

        {/* Right - Meta */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white">Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <span className="text-slate-200">{ticket.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Priority</span>
                <span className="text-slate-200">{ticket.priority}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Category</span>
                <span className="text-slate-200">{ticket.category || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Sentiment</span>
                <span className="text-slate-200">{ticket.sentiment || "—"}</span>
              </div>
            </div>
          </div>

          {!latestResponse && (
            <button
              onClick={handleProcess}
              disabled={processing}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50"
            >
              {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
              Run AI Pipeline
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
