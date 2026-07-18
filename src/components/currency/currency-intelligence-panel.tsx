"use client"

import { CurrencyAnalysisResult, SecurityFeature } from "@/lib/types/currency"
import { ShieldCheck, AlertTriangle, AlertCircle, CheckCircle2, Info, ArrowRight, ShieldAlert } from "lucide-react"

interface Props {
  verdict: CurrencyAnalysisResult | null
  onReset: () => void
}

export function CurrencyIntelligencePanel({ verdict, onReset }: Props) {
  if (!verdict) {
    return (
      <div className="flex flex-col min-h-[400px] lg:min-h-[500px] h-fit rounded-xl border border-shield-cyan/15 bg-shield-navy-light/50 p-5 shadow-xl shadow-shield-cyan/5 sm:p-6">
        <div className="flex flex-col items-center justify-center flex-1 text-center">
          <div className="mb-6 rounded-full bg-shield-cyan/5 p-4 ring-1 ring-shield-cyan/20">
            <ShieldCheck className="h-12 w-12 text-shield-cyan/50" />
          </div>
          <h3 className="text-lg font-semibold text-white">Intelligence Awaiting Analysis</h3>
          <p className="mt-2 max-w-[280px] text-sm text-shield-muted">
            Authenticity risk, visible security-feature observations, confidence information, and recommended actions will appear here.
          </p>
        </div>
      </div>
    )
  }

  // Determine status and risk level
  const isCounterfeit = verdict.status === "Counterfeit"
  const isSuspicious = verdict.status === "Suspicious"
  const isGenuine = verdict.status === "Genuine"
  
  const isHighRisk = verdict.risk_level === "High" || verdict.riskLevel === "High Risk"
  const isMediumRisk = verdict.risk_level === "Medium" || verdict.riskLevel === "Review Recommended"
  const isLowRisk = verdict.risk_level === "Low" || verdict.riskLevel === "Low Risk"

  const themeColor = isCounterfeit 
    ? "text-red-400 border-red-500/30 bg-red-500/10" 
    : isSuspicious
      ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
      : "text-green-400 border-green-500/30 bg-green-500/10"

  const strokeColor = isCounterfeit 
    ? "#f87171" 
    : isSuspicious
      ? "#fbbf24"
      : "#4ade80"

  const confidenceValue = verdict.confidence ?? verdict.confidenceScore ?? 0
  const circumference = 2 * Math.PI * 28
  const strokeDashoffset = circumference - (confidenceValue / 100) * circumference

  const renderFeatureStatusIcon = (status: SecurityFeature["status"]) => {
    switch (status) {
      case "Consistent":
        return <CheckCircle2 className="h-4 w-4 text-green-400" />
      case "Review":
        return <AlertTriangle className="h-4 w-4 text-amber-400" />
      case "Inconsistency":
        return <ShieldAlert className="h-4 w-4 text-red-400" />
      case "Unknown":
        return <Info className="h-4 w-4 text-shield-muted" />
    }
  }

  return (
    <div className="flex flex-col gap-5 h-fit rounded-xl border border-shield-cyan/15 bg-shield-navy-light/50 p-5 shadow-xl shadow-shield-cyan/5 sm:p-6 backdrop-blur-md">
      
      {/* Result Status Card */}
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-shield-muted">
          Analysis Status Verdict
        </h3>
        
        <div className={`relative flex items-center justify-between overflow-hidden rounded-xl border ${themeColor} p-4 bg-gradient-to-r ${
          isCounterfeit 
            ? "from-red-950/40 to-red-900/10" 
            : isSuspicious
              ? "from-amber-950/40 to-amber-900/10"
              : "from-green-950/40 to-green-900/10"
        }`}>
          <div className="z-10 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-3xl font-extrabold tracking-tight">
                {isCounterfeit ? "❌ Counterfeit" : isSuspicious ? "⚠️ Suspicious" : "✅ Genuine"}
              </span>
            </div>
            <p className="mt-1 text-xs opacity-75 font-medium">
              Denomination: {verdict.denomination} • Serial: {verdict.serial_number ?? "Not detected"}
            </p>
            <div className="mt-2 flex gap-3 text-[10px] text-slate-400">
              <span>Risk: <strong className={isCounterfeit ? "text-red-400" : isSuspicious ? "text-amber-400" : "text-green-400"}>{verdict.risk_level ?? (isHighRisk ? "High" : isMediumRisk ? "Medium" : "Low")}</strong></span>
              <span>•</span>
              <span>Time: {verdict.processing_time ?? "1.5 sec"}</span>
            </div>
          </div>

          <div className="relative z-10 flex flex-col items-center ml-2">
            <div className="relative flex h-16 w-16 items-center justify-center">
              <svg className="-rotate-90 transform" width="60" height="60">
                <circle
                  cx="30"
                  cy="30"
                  r="26"
                  stroke="currentColor"
                  strokeWidth="5"
                  fill="transparent"
                  className="opacity-20"
                />
                <circle
                  cx="30"
                  cy="30"
                  r="26"
                  stroke={strokeColor}
                  strokeWidth="5"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <span className="absolute text-xs font-extrabold">{confidenceValue}%</span>
            </div>
            <span className="mt-1 text-[9px] uppercase font-bold tracking-wider opacity-70">Confidence</span>
          </div>
        </div>
      </div>

      {/* Authenticity Mismatches / Verification Checks */}
      {verdict.authenticity_checks && verdict.authenticity_checks.some(c => !c.passed) && (
        <div className="rounded-lg border border-red-500/20 bg-red-950/20 p-4">
          <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4" /> Authenticity Violations Detected
          </h4>
          <div className="space-y-3">
            {verdict.authenticity_checks.filter(c => !c.passed).map((check, idx) => (
              <div key={idx} className="rounded-md border border-red-500/10 bg-red-950/30 p-3">
                <div className="text-xs font-bold text-slate-200 mb-2">
                  ❌ {check.check_name}
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded bg-red-500/15 p-2 border border-red-500/10">
                    <span className="block text-[10px] uppercase font-bold text-red-400/80 mb-0.5">Detected Text / Artwork</span>
                    <span className="font-mono text-red-300 break-words">"{check.detected}"</span>
                  </div>
                  <div className="rounded bg-green-500/15 p-2 border border-green-500/10">
                    <span className="block text-[10px] uppercase font-bold text-green-400/80 mb-0.5">Expected Official RBI</span>
                    <span className="font-mono text-green-300 break-words">"{check.expected}"</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}


      {/* Feature Detections Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-green-500/10 bg-green-950/10 p-3">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-green-400">Detected Features</span>
          <span className="text-xl font-extrabold text-green-400">{(verdict.detected_features ?? []).length}</span>
          <p className="mt-1 text-[10px] text-slate-400 truncate">
            {(verdict.detected_features ?? []).join(", ") || "None"}
          </p>
        </div>
        <div className="rounded-lg border border-red-500/10 bg-red-950/10 p-3">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-red-400">Missing/Suspicious</span>
          <span className="text-xl font-extrabold text-red-400">{(verdict.missing_features ?? []).length}</span>
          <p className="mt-1 text-[10px] text-slate-400 truncate">
            {(verdict.missing_features ?? []).join(", ") || "None"}
          </p>
        </div>
      </div>

      {/* Security Feature Checklist */}
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-shield-muted">
          Detailed Feature Analysis
        </h3>
        <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1">
          {verdict.features.map((feature, idx) => (
            <div key={idx} className="rounded-lg border border-shield-cyan/10 bg-shield-navy/40 p-2.5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-1.5">
                  {renderFeatureStatusIcon(feature.status)}
                  <span className="text-xs font-bold text-white">{feature.name}</span>
                </div>
                <div className={`rounded px-1.5 py-0.5 text-[9px] font-semibold ${
                  feature.status === "Consistent" ? "text-green-400 bg-green-500/10" :
                  feature.status === "Review" ? "text-amber-400 bg-amber-500/10" :
                  "text-red-400 bg-red-500/10"
                }`}>
                  {feature.status}
                </div>
              </div>
              <p className="mt-1 text-[11px] text-shield-muted leading-relaxed">
                {feature.observation}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* AI Explanation / Summary */}
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-shield-muted">
          AI Verdict Reasoning
        </h3>
        <div className="rounded-lg border border-shield-cyan/10 bg-shield-navy/20 p-3">
          <p className="text-xs text-shield-muted leading-relaxed">
            {verdict.authenticity_summary ?? verdict.authenticitySummary ?? "No verification explanation returned."}
          </p>
        </div>
      </div>

      {/* Recommendation Card */}
      <div className={`rounded-lg border ${themeColor} p-4`}>
        <div className="mb-2 flex items-center gap-2 font-bold text-xs uppercase tracking-wider">
          <Info className="h-4 w-4" /> Recommendation
        </div>
        <p className="text-xs opacity-90 leading-relaxed mb-4">
          {verdict.recommendation ?? (
            isLowRisk ? "No major visible inconsistencies were identified. Continue standard verification procedures." :
            "Potential visible inconsistencies identified. Do not rely solely on this result. Verify at the nearest bank or notify authorities."
          )}
        </p>

        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <button 
              onClick={onReset}
              className="flex-1 rounded border border-current bg-transparent px-3 py-2 text-xs font-bold hover:bg-current hover:bg-opacity-10 transition-colors"
            >
              Scan Another Note
            </button>
          </div>
          
          <div className="flex gap-2">
            <button 
              onClick={() => window.print()}
              className="flex-1 rounded border border-shield-muted/30 bg-shield-navy/50 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-shield-navy transition-colors flex items-center justify-center gap-1.5"
            >
              Download PDF Report
            </button>
            <button 
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: 'ShieldAI Currency Verification Result',
                    text: `Authenticity Status: ${verdict.status} (${confidenceValue}% confidence, Denomination: ${verdict.denomination})`,
                    url: window.location.href,
                  }).catch(console.error);
                } else {
                  navigator.clipboard.writeText(`ShieldAI Result: ${verdict.status} (${confidenceValue}% confidence, Denomination: ${verdict.denomination})`);
                  alert("Result copied to clipboard!");
                }
              }}
              className="flex-1 rounded border border-shield-muted/30 bg-shield-navy/50 px-3 py-2 text-xs font-bold text-slate-300 hover:bg-shield-navy transition-colors flex items-center justify-center gap-1.5"
            >
              Share Result
            </button>
          </div>
        </div>
      </div>

      {/* Responsible AI Disclaimer */}
      <div className="rounded bg-shield-navy/40 p-3 text-[10px] text-shield-muted/60 leading-relaxed text-center border border-shield-cyan/5">
        <AlertCircle className="inline-block h-3.5 w-3.5 mr-1 -mt-0.5" />
        {verdict.limitations ?? "This analysis is based solely on uploaded RGB images. It cannot conclusively authenticate currency or verify UV, infrared, magnetic, or tactile security features. Suspected counterfeit notes should always be verified using official RBI procedures or by an authorized bank."}
      </div>

    </div>
  )
}
