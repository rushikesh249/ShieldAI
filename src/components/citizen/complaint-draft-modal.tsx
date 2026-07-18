"use client"

import { useState, useEffect, useMemo } from "react"
import { ThreatVerdict, ThreatInput } from "@/lib/types/citizen"
import { Button } from "@/components/ui/button"
import { X, Copy, Printer, AlertTriangle, ShieldCheck } from "lucide-react"

interface Props {
  isOpen: boolean
  onClose: () => void
  verdict: ThreatVerdict | null
  input: ThreatInput
  t: Record<string, string>
}

export function ComplaintDraftModal({ isOpen, onClose, verdict, input, t }: Props) {
  const description = useMemo(() => {
    if (!verdict) return ''
    const template = t.complaint_template || ''
    return template
      .replace('{source}', input.source)
      .replace('{text}', input.text)
      .replace('{category}', verdict.category)
  }, [verdict, input, t])

  const [editableDescription, setEditableDescription] = useState('')

  useEffect(() => {
    setEditableDescription(description)
  }, [description])

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  if (!isOpen || !verdict) return null

  const handleCopy = () => {
    const textToCopy = `${t.modal_draft_title}\nDate: ${new Date().toLocaleDateString()}\n${t.label_incident_category}: ${verdict.category}\n${t.label_comm_source}: ${input.source}\n\n${editableDescription}\n\n${t.label_suspicious_entities}:\n${verdict.entities.map(e => `- ${e.type}: ${e.value}`).join("\n")}`
    navigator.clipboard.writeText(textToCopy)
    alert(t.toast_copy_success)
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
            <h2 id="modal-title" className="text-lg font-semibold text-white">{t.modal_draft_title}</h2>
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
                <h4 className="text-sm font-semibold text-shield-warning">{t.modal_review_warning_title}</h4>
                <p className="mt-1 text-xs text-shield-muted">{t.modal_review_warning_text}</p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_incident_category}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {verdict.category}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_incident_date}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {new Date().toLocaleDateString()}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_comm_source}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {input.source}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_threat_score}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-2.5 text-sm text-white print:border-gray-300 print:text-black">
                  {verdict.score}/100 ({verdict.level})
                </div>
              </div>
            </div>

            {verdict.entities.length > 0 && (
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_suspicious_entities}</label>
                <div className="rounded border border-shield-cyan/10 bg-shield-navy-light/30 p-3 print:border-gray-300">
                  <ul className="space-y-1">
                    {verdict.entities.map((e, idx) => (
                      <li key={idx} className="text-sm text-white print:text-black">
                        <span className="text-shield-muted print:text-gray-600">{e.type}:</span> {e.value}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase text-shield-muted">{t.label_description_editable}</label>
              <textarea
                value={editableDescription}
                onChange={(e) => setEditableDescription(e.target.value)}
                className="min-h-[160px] w-full rounded border border-shield-cyan/20 bg-shield-navy-light/30 p-3 text-sm text-white focus:border-shield-cyan focus:outline-none focus:ring-1 focus:ring-shield-cyan print:border-gray-300 print:text-black print:resize-none"
              />
            </div>
          </div>

        </div>

        <div className="flex flex-col-reverse justify-end gap-3 border-t border-shield-cyan/10 bg-shield-navy-light/50 p-4 sm:flex-row sm:px-6 print-hidden">
          <Button variant="outline" onClick={onClose} className="border-shield-cyan/20 text-white hover:bg-shield-navy-light">
            {t.btn_close}
          </Button>
          <Button variant="outline" onClick={handlePrint} className="border-shield-cyan/20 text-white hover:bg-shield-navy-light">
            <Printer className="mr-2 h-4 w-4" /> {t.btn_print}
          </Button>
          <Button onClick={handleCopy} className="bg-shield-cyan text-shield-navy hover:bg-shield-cyan/90">
            <Copy className="mr-2 h-4 w-4" /> {t.btn_copy}
          </Button>
        </div>
      </div>
    </div>
  )
}
