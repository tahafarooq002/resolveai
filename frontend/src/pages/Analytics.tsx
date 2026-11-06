import { useEffect, useState } from "react"
import { analyticsApi } from "../services/api"
import type { AnalyticsOverview } from "../types"

export default function Analytics() {
  const [stats, setStats] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi.overview()
      .then((res) => setStats(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    )
  }

  if (!stats) return <p className="text-slate-400">Failed to load analytics</p>

  const categories = Object.entries(stats.category_breakdown || {})

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">Performance metrics of your AI support system</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Tickets", value: stats.total_tickets },
          { label: "Resolved", value: stats.resolved_tickets },
          { label: "Pending Approval", value: stats.pending_approval },
          { label: "High Priority", value: stats.high_priority_tickets },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <p className="text-sm text-slate-400">{item.label}</p>
            <p className="mt-2 text-3xl font-bold text-white">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Approval Rate */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="text-sm font-semibold text-white">AI Response Quality</h3>
          <div className="mt-6 space-y-4">
            <div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Approval Rate</span>
                <span className="font-medium text-white">{stats.approval_rate_percent}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                  style={{ width: `${stats.approval_rate_percent}%` }}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-2xl font-bold text-white">{stats.approved_responses}</p>
                <p className="text-xs text-slate-500">Approved</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.low_confidence_responses}</p>
                <p className="text-xs text-slate-500">Low Confidence</p>
              </div>
            </div>
          </div>
        </div>

        {/* Categories */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="text-sm font-semibold text-white">Ticket Categories</h3>
          <div className="mt-4 space-y-3">
            {categories.length === 0 ? (
              <p className="text-sm text-slate-500">No data yet</p>
            ) : (
              categories.map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">{cat}</span>
                  <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-300">
                    {count}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
