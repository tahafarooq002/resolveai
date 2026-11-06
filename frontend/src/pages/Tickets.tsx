import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Plus, Search } from "lucide-react"
import { ticketsApi } from "../services/api"
import type { Ticket } from "../types"

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("")
  const [search, setSearch] = useState("")

  useEffect(() => {
    loadTickets()
  }, [statusFilter, search])

  const loadTickets = async () => {
    setLoading(true)
    try {
      const res = await ticketsApi.list({
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(search.trim() ? { search: search.trim() } : {}),
      })
      setTickets(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const priorityColor = (p: string) => {
    if (p === "critical" || p === "urgent" || p === "high") return "bg-rose-500/15 text-rose-400"
    if (p === "medium") return "bg-amber-500/15 text-amber-400"
    return "bg-slate-700 text-slate-300"
  }

  const statusColor = (s: string) => {
    if (s === "resolved") return "bg-emerald-500/15 text-emerald-400"
    if (s === "pending_approval") return "bg-indigo-500/15 text-indigo-400"
    return "bg-slate-700 text-slate-300"
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tickets</h1>
          <p className="mt-1 text-sm text-slate-400">Manage customer support requests</p>
        </div>
        <Link
          to="/tickets/new"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" /> New Ticket
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <label className="flex max-w-md flex-1 items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search subject or customer"
            className="w-full bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-600"
          />
        </label>
        <div className="flex gap-2">
        {["", "new", "processing", "pending_approval", "in_progress", "escalated", "resolved", "closed"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatusFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
              statusFilter === s
                ? "bg-indigo-500/20 text-indigo-300"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            {s === "" ? "All" : s.replace("_", " ")}
          </button>
        ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          </div>
        ) : tickets.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">No tickets found</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                <th className="px-6 py-3">Subject</th>
                <th className="px-6 py-3">Customer</th>
                <th className="px-6 py-3">Priority</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {tickets.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-6 py-4">
                    <Link to={`/tickets/${t.id}`} className="font-medium text-slate-200 hover:text-indigo-400">
                      {t.subject || "No subject"}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">{t.customer_name || t.customer_email || "—"}</td>
                  <td className="px-6 py-4">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${priorityColor(t.priority)}`}>
                      {t.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(t.status)}`}>
                      {t.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-400">{t.category || "—"}</td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {new Date(t.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
