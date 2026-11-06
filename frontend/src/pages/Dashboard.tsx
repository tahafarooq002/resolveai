import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  Ticket,
  CheckCircle,
  Clock,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
} from "lucide-react"
import { analyticsApi, ticketsApi } from "../services/api"
import type { AnalyticsOverview, Ticket as TicketType } from "../types"

export default function Dashboard() {
  const [stats, setStats] = useState<AnalyticsOverview | null>(null)
  const [recentTickets, setRecentTickets] = useState<TicketType[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, ticketsRes] = await Promise.all([
          analyticsApi.overview(),
          ticketsApi.list({ limit: 5 }),
        ])
        setStats(statsRes.data)
        setRecentTickets(ticketsRes.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const cards = [
    {
      label: "Total Tickets",
      value: stats?.total_tickets ?? 0,
      icon: Ticket,
      gradient: "from-blue-500 to-cyan-400",
      shadow: "shadow-blue-500/20",
      border: "hover:border-blue-500/40",
    },
    {
      label: "Resolved",
      value: stats?.resolved_tickets ?? 0,
      icon: CheckCircle,
      gradient: "from-emerald-500 to-teal-400",
      shadow: "shadow-emerald-500/20",
      border: "hover:border-emerald-500/40",
    },
    {
      label: "Pending Approval",
      value: stats?.pending_approval ?? 0,
      icon: Clock,
      gradient: "from-amber-500 to-orange-400",
      shadow: "shadow-amber-500/20",
      border: "hover:border-amber-500/40",
    },
    {
      label: "High Priority",
      value: stats?.high_priority_tickets ?? 0,
      icon: AlertTriangle,
      gradient: "from-rose-500 to-pink-400",
      shadow: "shadow-rose-500/20",
      border: "hover:border-rose-500/40",
    },
  ]

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Overview of your support operations
          </p>
        </div>
        <Link
          to="/tickets/new"
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:from-indigo-500 hover:to-violet-500"
        >
          + New Ticket
        </Link>
      </div>

      {/* Stats Cards - 3D style */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className={`group relative overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/70 p-5 shadow-xl backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${card.border} ${card.shadow}`}
          >
            {/* Glow effect */}
            <div
              className={`pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br ${card.gradient} opacity-20 blur-2xl transition group-hover:opacity-40`}
            />
            <div className="relative flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">{card.label}</p>
                <p className="mt-2 text-3xl font-bold tracking-tight text-white">
                  {card.value}
                </p>
              </div>
              <div
                className={`rounded-xl bg-gradient-to-br ${card.gradient} p-2.5 shadow-lg`}
              >
                <card.icon className="h-5 w-5 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Approval Rate Card */}
      {stats && (
        <div className="relative overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/70 p-6 shadow-xl backdrop-blur-sm">
          <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-indigo-500/20 blur-3xl" />
          <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-indigo-400" />
                <h3 className="text-sm font-medium text-slate-400">
                  AI Approval Rate
                </h3>
              </div>
              <p className="mt-2 text-3xl font-bold text-white">
                {stats.approval_rate_percent}%
              </p>
            </div>
            <div className="text-right text-sm text-slate-400">
              <p>
                <span className="font-medium text-white">
                  {stats.approved_responses}
                </span>{" "}
                approved
              </p>
              <p>
                <span className="font-medium text-white">
                  {stats.total_ai_responses}
                </span>{" "}
                total AI responses
              </p>
            </div>
          </div>
          <div className="relative mt-5 h-2.5 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 transition-all duration-700"
              style={{ width: `${Math.min(stats.approval_rate_percent, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Recent Tickets */}
      <div className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/70 shadow-xl backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <h3 className="font-semibold text-white">Recent Tickets</h3>
          <Link
            to="/tickets"
            className="flex items-center gap-1 text-sm text-indigo-400 transition hover:text-indigo-300"
          >
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="divide-y divide-slate-800">
          {recentTickets.length === 0 ? (
            <p className="px-6 py-10 text-center text-sm text-slate-500">
              No tickets yet. Create your first one!
            </p>
          ) : (
            recentTickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/tickets/${ticket.id}`}
                className="flex items-center justify-between px-6 py-4 transition hover:bg-slate-800/40"
              >
                <div>
                  <p className="font-medium text-slate-200">
                    {ticket.subject || ticket.customer_name || "Untitled"}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {ticket.customer_email} ·{" "}
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      ticket.priority === "high" || ticket.priority === "urgent"
                        ? "bg-rose-500/15 text-rose-400"
                        : "bg-slate-700/80 text-slate-300"
                    }`}
                  >
                    {ticket.priority}
                  </span>
                  <span className="rounded-full bg-slate-700/80 px-2.5 py-0.5 text-xs font-medium text-slate-300">
                    {ticket.status.replace("_", " ")}
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
