"use client"

import { AnalysisState, ThreatVerdict } from "@/lib/types/citizen"
import { useLanguage } from "@/lib/i18n/language-context"
import { ShieldCheck, Loader2, Info, CheckCircle2, AlertTriangle } from "lucide-react"

interface Props {
  state: AnalysisState
  verdict: ThreatVerdict | null
}

export function AnalysisWorkspace({ state, verdict }: Props) {
  const { t } = useLanguage()

  const STEPS = [
    { id: "validating", label: t("step_validating") },
    { id: "extracting", label: t("step_extracting") },
    { id: "analyzing", label: t("step_analyzing") },
    { id: "classifying", label: t("step_classifying") },
    { id: "recommending", label: t("step_recommending") }
  ]

  const isIdle = state === "idle"
  const isAnalyzing = state !== "idle" && state !== "complete" && state !== "error"
  const isComplete = state === "complete" && verdict !== null
  const isError = state === "error"

  return (
    <div className="flex flex-col min-h-[400px] lg:min-h-[560px] h-fit rounded-xl border border-shield-cyan/15 bg-shield-navy-light/80 p-5 shadow-2xl shadow-shield-cyan/5 backdrop-blur-sm sm:p-6">
      
      {/* Header */}
      <div className="mb-6 flex items-center justify-between border-b border-shield-cyan/10 pb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-shield-cyan" />
          <h2 className="text-lg font-semibold text-white">{t("analysis_engine_title")}</h2>
        </div>
        <div className="flex items-center gap-2">
          {isIdle && <span className="flex items-center gap-1.5 rounded-full border border-shield-cyan/20 bg-shield-cyan/10 px-2 py-0.5 text-[10px] font-medium text-shield-cyan"><span className="h-1.5 w-1.5 rounded-full bg-shield-cyan" /> {t("status_ready")}</span>}
          {isAnalyzing && <span className="flex items-center gap-1.5 rounded-full border border-shield-warning/20 bg-shield-warning/10 px-2 py-0.5 text-[10px] font-medium text-shield-warning"><Loader2 className="h-3 w-3 animate-spin" /> {t("status_processing")}</span>}
          {isComplete && <span className="flex items-center gap-1.5 rounded-full border border-shield-safe/20 bg-shield-safe/10 px-2 py-0.5 text-[10px] font-medium text-shield-safe"><CheckCircle2 className="h-3 w-3" /> {t("status_complete")}</span>}
          {isError && <span className="flex items-center gap-1.5 rounded-full border border-shield-critical/20 bg-shield-critical/10 px-2 py-0.5 text-[10px] font-medium text-shield-critical"><AlertTriangle className="h-3 w-3" /> {t("status_error")}</span>}
        </div>
      </div>

      <div className="flex flex-col justify-center flex-1">
        {/* Idle State */}
        {isIdle && (
          <div className="flex flex-col items-center text-center">
            <div className="mb-6 rounded-full bg-shield-cyan/5 p-4 ring-1 ring-shield-cyan/20">
              <ShieldCheck className="h-12 w-12 text-shield-cyan/50" />
            </div>
            <h3 className="text-lg font-semibold text-white">{t("idle_title")}</h3>
            <p className="mt-2 max-w-sm text-sm text-shield-muted">
              {t("idle_desc")}
            </p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="flex flex-col items-center text-center py-8">
            <div className="mb-4 rounded-full bg-shield-critical/10 p-4 ring-1 ring-shield-critical/30">
              <AlertTriangle className="h-10 w-10 text-shield-critical" />
            </div>
            <h3 className="text-lg font-semibold text-white">{t("error_title")}</h3>
            <p className="mt-2 max-w-sm text-sm text-shield-muted">
              {verdict?.assessment || "An error occurred while communicating with the analysis pipeline. Please check connection and try again."}
            </p>
          </div>
        )}

        {/* Analyzing State */}
        {isAnalyzing && (
          <div className="mx-auto w-full max-w-sm space-y-6">
            <div className="text-center">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-shield-cyan" />
              <p className="mt-4 text-sm font-medium text-white">{t("analyzing_title")}</p>
            </div>
            <div className="space-y-3">
              {STEPS.map((step, index) => {
                const stepIndex = STEPS.findIndex(s => s.id === state)
                const isPast = stepIndex > index
                const isCurrent = step.id === state
                
                return (
                  <div key={step.id} className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${isCurrent ? "border-shield-cyan/30 bg-shield-cyan/10" : isPast ? "border-shield-safe/20 bg-shield-safe/5" : "border-shield-cyan/5 bg-shield-navy/20"}`}>
                    {isPast ? <CheckCircle2 className="h-4 w-4 text-shield-safe" /> : isCurrent ? <Loader2 className="h-4 w-4 animate-spin text-shield-cyan" /> : <div className="h-4 w-4 rounded-full border-2 border-shield-muted/30" />}
                    <span className={`text-xs font-medium ${isCurrent ? "text-shield-cyan" : isPast ? "text-shield-safe/80" : "text-shield-muted/50"}`}>{step.label}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Complete State */}
        {isComplete && verdict && (
          <div className="flex h-full flex-col">
            <div className="mb-6 text-center">
              <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-shield-muted/70">{t("verdict_title")}</div>
              <h3 className={`text-3xl font-bold ${
                verdict.level === "Critical" || verdict.level === "High-Risk" ? "text-shield-critical" :
                verdict.level === "Suspicious" || verdict.level === "Caution" ? "text-shield-warning" :
                "text-shield-safe"
              }`}>
                {verdict.level}
              </h3>
            </div>

            <div className="mb-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-shield-cyan/10 bg-shield-navy/40 p-4 text-center">
                <div className="text-[10px] uppercase text-shield-muted">{t("threat_score")}</div>
                <div className="mt-1 text-2xl font-bold text-white">{verdict.score}<span className="text-sm text-shield-muted">/100</span></div>
              </div>
              <div className="rounded-lg border border-shield-cyan/10 bg-shield-navy/40 p-4 text-center">
                <div className="text-[10px] uppercase text-shield-muted">{t("model_confidence")}</div>
                <div className="mt-1 text-2xl font-bold text-white">{verdict.confidence}<span className="text-sm text-shield-muted">%</span></div>
              </div>
            </div>

            <div className="mb-4 rounded-lg border border-shield-cyan/20 bg-shield-cyan/5 p-4">
              <div className="mb-2 flex items-center gap-2">
                <Info className="h-4 w-4 text-shield-cyan" />
                <span className="text-xs font-semibold uppercase text-shield-cyan">{t("ai_risk_assessment")}</span>
              </div>
              <p className="text-sm leading-relaxed text-shield-muted">{verdict.assessment}</p>
            </div>
            
            <div className="mt-auto flex items-center justify-between border-t border-shield-cyan/10 pt-4 text-[10px] text-shield-muted">
              <span>{t("category")}: <strong className="text-white">{verdict.category}</strong></span>
              <span>{t("completed_at", { time: new Date(verdict.timestamp).toLocaleTimeString() })}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
