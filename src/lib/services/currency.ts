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
  if (!input.imageFile) {
    throw new Error("No image file provided.")
  }
  
  onStateChange("preparing")
  await sleep(300)
  
  onStateChange("detecting")
  await sleep(300)
  
  onStateChange("inspecting")
  await sleep(300)
  
  onStateChange("generating")

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1"

  try {
    const formData = new FormData()
    formData.append("file", input.imageFile)
    formData.append("denomination", input.denomination)
    formData.append("note_side", input.noteSide)

    const response = await fetch(`${apiUrl}/currency/counterfeit-detection`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      const errorJson = await response.json().catch(() => ({}))
      const errorMsg = errorJson.message || "Failed to analyze note."
      throw new Error(errorMsg)
    }

    const json = await response.json()
    const result = json.data as CurrencyAnalysisResult

    onStateChange("complete")
    return result
  } catch (error) {
    onStateChange("error")
    console.error("Currency counterfeit detection failed:", error)
    throw error
  }
}
