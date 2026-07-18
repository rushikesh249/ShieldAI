export type CurrencyDenomination = "₹10" | "₹20" | "₹50" | "₹100" | "₹200" | "₹500" | "₹2000"
export type CurrencyNoteSide = "Front" | "Reverse"
export type CaptureType = "Single Image" | "Front + Reverse"

export interface CurrencyInput {
  imageFile: File | null
  imagePreviewUrl: string | null
  denomination: CurrencyDenomination
  noteSide: CurrencyNoteSide
  captureType: CaptureType
}

export type FeatureStatus = "Consistent" | "Review" | "Inconsistency" | "Unknown"

export interface BoundingBox {
  x: number  // normalized 0.0–1.0
  y: number
  width: number
  height: number
}

export interface SecurityFeature {
  id: string
  name: string
  status: FeatureStatus
  observation: string
  confidence?: number // 0-100
  boundingBox?: BoundingBox // real coordinates from Gemini
}

export type CurrencyRiskLevel = "Low Risk" | "Review Recommended" | "High Risk"

export interface AuthenticityCheck {
  check_name: string
  passed: boolean
  detected: string
  expected: string
}

export interface CurrencyAnalysisResult {
  id?: string
  status: "Genuine" | "Counterfeit" | "Suspicious"
  confidence: number // 0-100
  denomination: string
  serial_number: string
  detected_features: string[]
  missing_features: string[]
  risk_level: "High" | "Medium" | "Low"
  processing_time: string
  recommendation: string
  limitations: string
  features: SecurityFeature[]
  authenticity_checks?: AuthenticityCheck[]
  authenticity_summary?: string
  image_url?: string
  timestamp?: string
  
  // Backward compatibility fields
  riskLevel?: CurrencyRiskLevel
  confidenceScore?: number
  genuineIndicators?: string[]
  counterfeitIndicators?: string[]
  authenticitySummary?: string
  evidence?: string[]
}


export type CurrencyAnalysisState = 
  | "idle"
  | "preparing"
  | "detecting"
  | "inspecting"
  | "generating"
  | "complete"
  | "error"
