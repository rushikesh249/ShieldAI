"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Footer } from "@/components/footer"
import { ThreatInputWorkspace } from "@/components/citizen/threat-input-workspace"
import { AnalysisWorkspace } from "@/components/citizen/analysis-workspace"
import { IntelligenceWorkspace } from "@/components/citizen/intelligence-workspace"
import { ComplaintDraftModal } from "@/components/citizen/complaint-draft-modal"
import { ThreatInput, AnalysisState, ThreatVerdict } from "@/lib/types/citizen"
import { analyzeThreat } from "@/lib/services/analysis"
import { LanguageProvider, useLanguage } from "@/lib/i18n/language-context"
import { LanguageSelector } from "@/components/language-selector"

function CitizenContent() {
  const { t } = useLanguage()
  const [input, setInput] = useState<ThreatInput>({
    source: "WhatsApp",
    text: "",
    file: null,
  })
  
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle")
  const [verdict, setVerdict] = useState<ThreatVerdict | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleInputChange = (updates: Partial<ThreatInput>) => {
    setInput(prev => ({ ...prev, ...updates }))
    if (analysisState !== "idle") {
      setAnalysisState("idle")
      setVerdict(null)
    }
  }

  const handleAnalyze = async () => {
    setVerdict(null)
    setAnalysisState("validating")
    
    try {
      const result = await analyzeThreat(input, setAnalysisState)
      setVerdict(result)
    } catch (error) {
      console.error(error)
      setAnalysisState("error")
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-shield-navy selection:bg-shield-cyan/30">
      {/* Background Effects */}
      <div className="pointer-events-none fixed inset-0 flex justify-center bg-shield-navy">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
      </div>

      <Navigation />

      <main className="relative flex-1 pt-24 pb-8 lg:pt-24">
        <div className="mx-auto max-w-[1600px] px-4 sm:px-6 lg:px-8">
          
          {/* Header & Language Selector */}
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-shield-cyan/10 pb-4 gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">{t("page_title")}</h1>
              <p className="text-sm text-shield-muted">{t("page_subtitle")}</p>
            </div>
            
            <LanguageSelector />
          </div>

          {/* 3-Zone Workspace */}
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-[minmax(340px,1.05fr)_minmax(380px,1.1fr)_minmax(340px,1fr)] lg:gap-6 lg:items-start">
            {/* Left Zone: Input */}
            <div>
              <ThreatInputWorkspace 
                input={input}
                onInputChange={handleInputChange}
                onAnalyze={handleAnalyze}
                isAnalyzing={analysisState !== "idle" && analysisState !== "complete" && analysisState !== "error"}
              />
            </div>

            {/* Center Zone: Analysis */}
            <div className="order-first md:order-none md:col-span-2 lg:col-span-1">
              <AnalysisWorkspace 
                state={analysisState}
                verdict={verdict}
              />
            </div>

            {/* Right Zone: Intelligence */}
            <div>
              <IntelligenceWorkspace 
                verdict={verdict}
                onGenerateDraft={() => setIsModalOpen(true)}
              />
            </div>
          </div>

        </div>
      </main>

      <Footer />

      <ComplaintDraftModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        verdict={verdict}
        input={input}
      />
    </div>
  )
}

export default function CitizenPage() {
  return (
    <LanguageProvider>
      <CitizenContent />
    </LanguageProvider>
  )
}
