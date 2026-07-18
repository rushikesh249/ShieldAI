import { CurrencyInput, CurrencyAnalysisState, CurrencyAnalysisResult } from "@/lib/types/currency"

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * DEMO FRONTEND ANALYSIS — REPLACE WITH REAL MODEL RESPONSE
 * 
 * This function simulates an AI vision pipeline inspecting currency security features.
 * Replace this with actual calls to TensorFlow.js or Gemini Vision API in the future.
 */
export async function analyzeCurrency(
  input: CurrencyInput,
  onStateChange: (state: CurrencyAnalysisState) => void
): Promise<CurrencyAnalysisResult> {
  
  onStateChange("preparing")
  await sleep(600)
  
  onStateChange("detecting")
  await sleep(800)
  
  onStateChange("inspecting")
  await sleep(900)
  
  onStateChange("generating")
  await sleep(700)

  onStateChange("complete")
  
  // Return a mock result. In a real system, this would evaluate the image and model output.
  // We'll generate a random realistic result for demonstration purposes.
  
  // Generate a random outcome based on math.random for demo purposes.
  // 60% chance Low Risk, 30% Review, 10% High Risk
  const random = Math.random()
  
  if (random < 0.6) {
    return {
      riskLevel: "Low Risk",
      confidenceScore: 92,
      features: [
        { id: "watermark", name: "Watermark", status: "Consistent", observation: "Watermark region appears consistent with the selected denomination.", confidence: 95 },
        { id: "security-thread", name: "Security Thread", status: "Consistent", observation: "A continuous vertical security thread is visible.", confidence: 88 },
        { id: "rbi-seal", name: "RBI Seal", status: "Consistent", observation: "Seal placement and proportions match standard currency templates.", confidence: 90 },
      ],
      evidence: [
        `Note structure appears aligned with the selected denomination (${input.denomination})`,
        "No major visible inconsistencies were identified in the security regions.",
        "Color profile and contrast fall within acceptable bounds."
      ]
    }
  } else if (random < 0.9) {
    return {
      riskLevel: "Review Recommended",
      confidenceScore: 68,
      features: [
        { id: "watermark", name: "Watermark", status: "Review", observation: "Watermark region requires clearer lighting to confirm details.", confidence: 60 },
        { id: "security-thread", name: "Security Thread", status: "Consistent", observation: "A continuous vertical security thread is visible.", confidence: 85 },
        { id: "serial", name: "Serial Number", status: "Review", observation: "Serial number print alignment is partially obscured by glare or wear.", confidence: 55 },
      ],
      evidence: [
        "Image glare or low lighting reduced confidence in watermark inspection.",
        "Some micro-print regions lack sufficient sharpness.",
        "Capture both sides in better lighting or request manual verification."
      ]
    }
  } else {
    return {
      riskLevel: "High Risk",
      confidenceScore: 24,
      features: [
        { id: "watermark", name: "Watermark", status: "Inconsistency", observation: "Expected watermark silhouette is missing or misaligned.", confidence: 85 },
        { id: "security-thread", name: "Security Thread", status: "Inconsistency", observation: "Security thread appears painted or lacks expected continuous metallic properties.", confidence: 90 },
        { id: "color-shift", name: "Color-Shift Ink", status: "Review", observation: "Unable to verify optical variable ink properties from a single static image.", confidence: 40 },
      ],
      evidence: [
        "Potential visible inconsistencies identified in the security thread region.",
        "Watermark profile does not match expected patterns.",
        "Do not rely solely on this result. Follow authorized verification procedures."
      ]
    }
  }
}
