"use client"

import { useState, useEffect } from "react"
import { ThreatVerdict, ThreatInput } from "@/lib/types/citizen"
import { useLanguage } from "@/lib/i18n/language-context"
import { Button } from "@/components/ui/button"
import { X, Copy, Printer, AlertTriangle, ShieldCheck } from "lucide-react"

interface Props {
  isOpen: boolean
  onClose: () => void
  verdict: ThreatVerdict | null
  input: ThreatInput
}

export function ComplaintDraftModal({ isOpen, onClose, verdict, input }: Props) {
  const { t } = useLanguage()
  const [description, setDescription] = useState("")

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = "unset"
    }
    return () => {
      document.body.style.overflow = "unset"
    }
  }, [isOpen])

  useEffect(() => {
    if (verdict) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDescription(t("complaint_narrative_template", {
        source: input.source,
        text: input.text || "Screenshot / File Evidence",
        category: verdict.category
      }))
    }
  }, [verdict, input, t])

  if (!isOpen || !verdict) return null

  const handleCopy = () => {
    const textToCopy = `Incident Report Draft
Date: ${new Date().toLocaleDateString()}
Category: ${verdict.category}
Source: ${input.source}

Description:
${description}

Entities Involved:
${verdict.entities.map(e => `- ${e.type}: ${e.value}`).join("\n")}
`
    navigator.clipboard.writeText(textToCopy)
    alert(t("draft_copied_toast"))
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-shield-navy/80 backdrop-blur-sm print:bg-white print:p-0">
      
      {/* Print-only CSS injection */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          #printable-complaint, #printable-complaint * {
            visibility: visible;
            color: black !important;
            background: white !important;
            border-color: #ccc !important;
          }
          #printable-complaint {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: auto;
            overflow: visible;
            padding: 2cm;
          }
          .print-hidden {
            display: none !important;
          }
        }
      `}</style>

      <div 
        role="dialog" 
        aria-modal="true"
        aria-labelledby="modal-title"
        className="relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-shield-cyan/20 bg-shield-navy shadow-2xl print:border-none print:shadow-none"
      >
        <div className="flex items-center justify-between border-b border-shield-cyan/10 bg-shield-navy-light/50 p-4 sm:px-6 print-hidden">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-shield-cyan" />
            <h2 id="modal-title" className="text-lg font-semibold text-white">{t("modal_title")}</h2>
          </div>
          <button 
            onClick={onClose}
            className="rounded-lg p-1 text-shield-muted transition-colors hover:bg-shield-cyan/10 hover:text-white"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto p-4 sm:p-6" id="printable-complaint">
          
          <div className="mb-6 rounded-lg border border-shield-warning/30 bg-shield-warning/10 p-4 print-hidden">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 text-shield-warning" />
              <div>
                <h4 className="text-sm font-semibold text-shield-warning">{t("review_warning_title")}</h4>
                <p className="mt-1 text-xs text-shield-muted">{t("review_warning_desc")}</p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("incident_category")}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {verdict.category}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("incident_date")}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {new Date().toLocaleDateString()}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("comm_source")}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {input.source}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("threat_score")}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {verdict.score}/100 ({verdict.level})
                </div>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("incident_description")}</label>
              <textarea 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="h-36 w-full resize-none rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-3 text-sm text-white focus:border-shield-cyan/40 focus:outline-none print:border-gray-300 print:text-black"
              />
            </div>

            {verdict.entities.length > 0 && (
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t("entities_involved")}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-3 space-y-1 print:border-gray-300 print:text-black">
                  {verdict.entities.map((e, idx) => (
                    <div key={idx} className="text-xs text-shield-muted print:text-black">
                      <strong className="text-white print:text-black">{e.type}:</strong> {e.value}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>

        <div className="flex items-center justify-end gap-3 border-t border-shield-cyan/10 bg-shield-navy-light/30 p-4 sm:px-6 print-hidden">
          <Button 
            onClick={handlePrint}
            variant="outline"
            className="border-shield-cyan/20 text-white hover:bg-shield-cyan/10"
          >
            <Printer className="mr-2 h-4 w-4" />
            {t("print_draft_btn")}
          </Button>
          <Button 
            onClick={handleCopy}
            className="bg-shield-cyan text-shield-navy hover:bg-shield-cyan/90 font-semibold"
          >
            <Copy className="mr-2 h-4 w-4" />
            {t("copy_draft_btn")}
          </Button>
        </div>

      </div>
    </div>
  )
}
