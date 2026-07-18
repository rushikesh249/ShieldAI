"use client"

import { useEffect, useState } from "react"
import { Shield, TrendingUp, AlertTriangle, CheckCircle2, Users, FileDown } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface AdminStats {
  totalScans: number
  fakeDetected: number
  genuineDetected: number
  averageConfidence: number
  dailyAnalytics: { date: string; scans: number }[]
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/admin/stats")
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error("Failed to fetch admin stats:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 pt-24 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300 flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              Admin Analytics
            </h1>
            <p className="text-slate-400 mt-2">Platform usage and threat detection metrics.</p>
          </div>
          <div className="flex gap-3">
            <button className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg transition-colors text-sm font-medium border border-slate-700">
              <FileDown className="w-4 h-4" /> Export CSV
            </button>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium">
              <FileDown className="w-4 h-4" /> Export PDF
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center p-20"><div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : stats ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Total Scans</CardTitle>
                  <Shield className="w-4 h-4 text-blue-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-100">{stats.totalScans}</div>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Fake Detected</CardTitle>
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-rose-400">{stats.fakeDetected}</div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Genuine Detected</CardTitle>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-emerald-400">{stats.genuineDetected}</div>
                </CardContent>
              </Card>

              <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-slate-400">Avg. Confidence</CardTitle>
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-slate-100">{stats.averageConfidence}%</div>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-xl font-medium text-slate-200">Daily Scans (Last 30 Days)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full flex items-end gap-2 pt-4">
                  {stats.dailyAnalytics.map((day, i) => {
                    const maxScans = Math.max(...stats.dailyAnalytics.map(d => d.scans), 1)
                    const height = `${(day.scans / maxScans) * 100}%`
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-2 group relative">
                        <div 
                          className="w-full bg-blue-500/20 hover:bg-blue-400/50 transition-colors rounded-t-sm"
                          style={{ height }}
                        />
                        <div className="text-[10px] text-slate-500 rotate-45 origin-left whitespace-nowrap">{day.date.substring(5)}</div>
                        <div className="absolute -top-8 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                          {day.scans}
                        </div>
                      </div>
                    )
                  })}
                  {stats.dailyAnalytics.length === 0 && (
                    <div className="w-full h-full flex items-center justify-center text-slate-500">No data available</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="text-center p-8 text-rose-400">Failed to load analytics data.</div>
        )}
      </div>
    </div>
  )
}
