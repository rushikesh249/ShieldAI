"use client"

import { useEffect, useState } from "react"
import { Shield, Trash2, Download, Search, AlertCircle, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ScanHistory {
  id: string
  timestamp: string
  prediction: string
  confidenceScore: number
  image_url: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<ScanHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/history/")
      const data = await res.json()
      setHistory(data)
    } catch (err) {
      console.error("Failed to fetch history:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/v1/history/${id}`, { method: "DELETE" })
      setHistory(history.filter(h => h.id !== id))
    } catch (err) {
      console.error("Failed to delete", err)
    }
  }

  const filteredHistory = history.filter(h => h.id.includes(search) || h.prediction.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 pt-24 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300 flex items-center gap-2">
              <Shield className="w-8 h-8 text-blue-400" />
              Scan History
            </h1>
            <p className="text-slate-400 mt-2">View and manage your previous currency verifications.</p>
          </div>
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search scans..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-xl font-medium text-slate-200">Recent Scans</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center p-8"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>
            ) : filteredHistory.length === 0 ? (
              <div className="text-center p-8 text-slate-500">No scans found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="pb-3 font-medium">Scan ID</th>
                      <th className="pb-3 font-medium">Date & Time</th>
                      <th className="pb-3 font-medium">Result</th>
                      <th className="pb-3 font-medium">Confidence</th>
                      <th className="pb-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {filteredHistory.map((scan) => (
                      <tr key={scan.id} className="hover:bg-slate-800/20 transition-colors group">
                        <td className="py-4 font-mono text-xs text-slate-400">{scan.id}</td>
                        <td className="py-4">{new Date(scan.timestamp).toLocaleString()}</td>
                        <td className="py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                            scan.prediction === 'Low Risk' || scan.prediction === 'Genuine' 
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          }`}>
                            {scan.prediction === 'Low Risk' || scan.prediction === 'Genuine' ? <CheckCircle2 className="w-3.5 h-3.5"/> : <AlertCircle className="w-3.5 h-3.5"/>}
                            {scan.prediction}
                          </span>
                        </td>
                        <td className="py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${scan.prediction === 'Low Risk' || scan.prediction === 'Genuine' ? 'bg-emerald-500' : 'bg-rose-500'}`}
                                style={{ width: `${scan.confidenceScore}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400">{scan.confidenceScore}%</span>
                          </div>
                        </td>
                        <td className="py-4 text-right">
                          <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-400/10 rounded-md transition-colors" title="Download Report">
                              <Download className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleDelete(scan.id)} className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 rounded-md transition-colors" title="Delete Record">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
