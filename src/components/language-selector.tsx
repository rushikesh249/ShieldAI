"use client"

import { useState, useRef, useEffect } from "react"
import { useLanguage, INDIAN_LANGUAGES } from "@/lib/i18n/language-context"
import { Globe, Search, Check, ChevronDown } from "lucide-react"

export function LanguageSelector() {
  const { language, setLanguage, currentLanguage, t } = useLanguage()
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false)
    }

    document.addEventListener("mousedown", handleClickOutside)
    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [])

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  const filteredLanguages = INDIAN_LANGUAGES.filter(lang => 
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-shield-cyan/30 bg-shield-navy-light/80 px-3 py-1.5 text-xs font-semibold text-white shadow-lg transition-all hover:border-shield-cyan/60 hover:bg-shield-cyan/10 focus:outline-none"
        aria-label={t("select_language")}
        aria-expanded={isOpen}
      >
        <Globe className="h-4 w-4 text-shield-cyan animate-pulse" />
        <span className="flex items-center gap-1.5">
          <span className="font-bold text-shield-cyan">{currentLanguage.nativeName}</span>
          <span className="text-[10px] text-shield-muted hidden sm:inline">({currentLanguage.name})</span>
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-shield-muted transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 z-50 w-72 rounded-xl border border-shield-cyan/20 bg-shield-navy/98 p-2.5 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-150">
          
          {/* Header & Search */}
          <div className="mb-2">
            <div className="flex items-center justify-between px-2 pb-1.5 text-[11px] font-semibold text-shield-muted border-b border-shield-cyan/10">
              <span>{t("select_language")}</span>
              <span className="rounded bg-shield-cyan/10 px-1.5 py-0.5 text-[10px] text-shield-cyan font-bold">23 Languages</span>
            </div>
            
            <div className="relative mt-2">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-shield-muted" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("search_languages")}
                className="w-full rounded-md border border-shield-cyan/15 bg-shield-navy-light/60 py-1.5 pl-8 pr-3 text-xs text-white placeholder-shield-muted/50 focus:border-shield-cyan/50 focus:outline-none"
              />
            </div>
          </div>

          {/* Languages Grid / List */}
          <div className="max-h-64 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {filteredLanguages.length > 0 ? (
              filteredLanguages.map((lang) => {
                const isSelected = language === lang.code
                return (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setLanguage(lang.code)
                      setIsOpen(false)
                      setSearchQuery("")
                    }}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${
                      isSelected
                        ? "bg-shield-cyan/20 font-bold text-white border border-shield-cyan/40"
                        : "text-shield-muted hover:bg-shield-cyan/10 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{lang.flag}</span>
                      <div className="flex flex-col">
                        <span className="font-medium text-white">{lang.nativeName}</span>
                        <span className="text-[10px] text-shield-muted">{lang.name}</span>
                      </div>
                    </div>
                    {isSelected && <Check className="h-4 w-4 text-shield-cyan" />}
                  </button>
                )
              })
            ) : (
              <div className="p-3 text-center text-xs text-shield-muted">
                No matching language found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
