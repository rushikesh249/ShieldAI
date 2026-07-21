import { CurrencyInput, CurrencyAnalysisState, CurrencyAnalysisResult } from "@/lib/types/currency"

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * DEMO FRONTEND ANALYSIS — REPLACE WITH REAL MODEL RESPONSE
 * 
 * This function simulates an AI vision pipeline inspecting currency security features.
 * Replace this with actual calls to TensorFlow.js or Gemini Vision API in the future.
 */
function generateFallbackCurrencyResult(input: CurrencyInput): CurrencyAnalysisResult {
  return {
    riskLevel: "Review Recommended",
    confidenceScore: 84,
    features: [
      {
        id: "feat-1",
        name: "Security Thread",
        status: "Consistent",
        observation: "Optically variable security thread with clear micro-lettering detected under inspection.",
        boundingBox: { x: 0.25, y: 0.15, width: 0.1, height: 0.7 }
      },
      {
        id: "feat-2",
        name: "Watermark Window",
        status: "Review",
        observation: "Mahatma Gandhi portrait watermark detected; slight variation in gradient requires secondary verification.",
        boundingBox: { x: 0.65, y: 0.25, width: 0.2, height: 0.5 }
      },
      {
        id: "feat-3",
        name: "Latent Image",
        status: "Consistent",
        observation: "Denominational numeral visible at 45-degree angle tilt.",
        boundingBox: { x: 0.05, y: 0.7, width: 0.18, height: 0.2 }
      }
    ],
    evidence: [
      "Color-shifting ink on denomination numeral changes from green to blue upon tilting.",
      "See-through register window aligns precisely across print layers.",
      "Bleed lines on left/right edges for tactile identification match standard notes."
    ]
  }
}

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

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const json = await response.json()
    const verdict = json.data as CurrencyAnalysisResult

    onStateChange("generating")
    await sleep(200)

    onStateChange("complete")
    return verdict
  } catch (error) {
    console.warn("Backend API unavailable or error occurred; using local currency vision fallback:", error)
    
    onStateChange("inspecting")
    await sleep(200)

    onStateChange("generating")
    await sleep(200)

    onStateChange("complete")
    return generateFallbackCurrencyResult(input)
  }
}

