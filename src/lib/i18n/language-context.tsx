"use client"

import React, { createContext, useContext, useState, useEffect } from "react"
import { translations, TranslationKey, LanguageCode } from "./translations"

export interface LanguageOption {
  code: LanguageCode
  name: string
  nativeName: string
  speechLocale: string
  flag: string
}

export const INDIAN_LANGUAGES: LanguageOption[] = [
  { code: "en", name: "English", nativeName: "English", speechLocale: "en-IN", flag: "🇮🇳" },
  { code: "hi", name: "Hindi", nativeName: "हिंदी", speechLocale: "hi-IN", flag: "🇮🇳" },
  { code: "bn", name: "Bengali", nativeName: "বাংলা", speechLocale: "bn-IN", flag: "🇮🇳" },
  { code: "te", name: "Telugu", nativeName: "తెలుగు", speechLocale: "te-IN", flag: "🇮🇳" },
  { code: "mr", name: "Marathi", nativeName: "मराठी", speechLocale: "mr-IN", flag: "🇮🇳" },
  { code: "ta", name: "Tamil", nativeName: "தமிழ்", speechLocale: "ta-IN", flag: "🇮🇳" },
  { code: "gu", name: "Gujarati", nativeName: "ગુજરાતી", speechLocale: "gu-IN", flag: "🇮🇳" },
  { code: "ur", name: "Urdu", nativeName: "اردو", speechLocale: "ur-IN", flag: "🇮🇳" },
  { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ", speechLocale: "kn-IN", flag: "🇮🇳" },
  { code: "or", name: "Odia", nativeName: "ଓଡ଼ିଆ", speechLocale: "or-IN", flag: "🇮🇳" },
  { code: "ml", name: "Malayalam", nativeName: "മലയാളം", speechLocale: "ml-IN", flag: "🇮🇳" },
  { code: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ", speechLocale: "pa-IN", flag: "🇮🇳" },
  { code: "as", name: "Assamese", nativeName: "অসমীয়া", speechLocale: "as-IN", flag: "🇮🇳" },
  { code: "mai", name: "Maithili", nativeName: "मैथिली", speechLocale: "hi-IN", flag: "🇮🇳" },
  { code: "sa", name: "Sanskrit", nativeName: "संस्कृतम्", speechLocale: "sa-IN", flag: "🇮🇳" },
  { code: "kok", name: "Konkani", nativeName: "कोंकणी", speechLocale: "kok-IN", flag: "🇮🇳" },
  { code: "ne", name: "Nepali", nativeName: "नेपाली", speechLocale: "ne-IN", flag: "🇮🇳" },
  { code: "sd", name: "Sindhi", nativeName: "सिंधी", speechLocale: "sd-IN", flag: "🇮🇳" },
  { code: "doi", name: "Dogri", nativeName: "डोगरी", speechLocale: "hi-IN", flag: "🇮🇳" },
  { code: "mni", name: "Manipuri", nativeName: "ꯃꯅꯤꯄꯨꯔꯤ", speechLocale: "mni-IN", flag: "🇮🇳" },
  { code: "brx", name: "Bodo", nativeName: "बडो", speechLocale: "hi-IN", flag: "🇮🇳" },
  { code: "sat", name: "Santali", nativeName: "ᱥᱟᱱᱛᱟᱲᱤ", speechLocale: "hi-IN", flag: "🇮🇳" },
  { code: "ks", name: "Kashmiri", nativeName: "کٲشُر", speechLocale: "ur-IN", flag: "🇮🇳" },
]

interface LanguageContextType {
  language: LanguageCode
  setLanguage: (code: LanguageCode) => void
  currentLanguage: LanguageOption
  t: (key: TranslationKey, params?: Record<string, string | number>) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("en")

  useEffect(() => {
    const saved = localStorage.getItem("shieldai_language") as LanguageCode
    if (saved && INDIAN_LANGUAGES.some(l => l.code === saved)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLanguageState(saved)
    }
  }, [])

  const setLanguage = (code: LanguageCode) => {
    setLanguageState(code)
    try {
      localStorage.setItem("shieldai_language", code)
    } catch {
      // localStorage may be disabled
    }
  }

  const currentLanguage = INDIAN_LANGUAGES.find(l => l.code === language) || INDIAN_LANGUAGES[0]

  const t = (key: TranslationKey, params?: Record<string, string | number>): string => {
    const langDict = translations[language] || translations["en"]
    let text = langDict[key] || translations["en"][key] || key
    if (params) {
      Object.entries(params).forEach(([pKey, pVal]) => {
        text = text.replace(new RegExp(`\\{${pKey}\\}`, "g"), String(pVal))
      })
    }
    return text
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, currentLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
