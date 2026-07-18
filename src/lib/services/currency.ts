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
  await sleep(300)
  
  onStateChange("detecting")
  await sleep(300)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

  try {
    if (!input.imageFile) {
      throw new Error("No image file provided")
    }

    onStateChange("inspecting")

    const formData = new FormData()
    formData.append("file", input.imageFile)
    formData.append("denomination", input.denomination)
    formData.append("note_side", input.noteSide)

    const response = await fetch(`${apiUrl}/currency/analyze`, {
      method: "POST",
      body: formData,
    })

    onStateChange("generating")
    await sleep(200)

    if (!response.ok) {
      throw new Error("Failed to analyze currency")
    }

    const json = await response.json()
    const verdict = json.data as CurrencyAnalysisResult

    onStateChange("complete")
    return verdict
  } catch (error) {
    onStateChange("error")
    console.error("Currency analysis failed:", error)
    // Fallback to error state
    return {
      riskLevel: "Review Recommended",
      confidenceScore: 0,
      features: [],
      evidence: ["Analysis failed. Please check your backend connection."],
    }
  }
}
