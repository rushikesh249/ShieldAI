import { AnalysisState, ThreatInput, ThreatVerdict } from "@/lib/types/citizen"

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export async function analyzeThreat(
  input: ThreatInput,
  onStateChange: (state: AnalysisState) => void
): Promise<ThreatVerdict> {
  // Simulate API pipeline states for UI feedback
  onStateChange("validating")
  await sleep(300)
  
  onStateChange("extracting")
  await sleep(300)
  
  onStateChange("analyzing")

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

  try {
    let response;
    
    if (input.file) {
      // Analyze Image
      const formData = new FormData()
      formData.append("file", input.file)
      
      response = await fetch(`${apiUrl}/fraud/analyze-image`, {
        method: "POST",
        body: formData,
      })
    } else {
      // Analyze Text
      const payload = {
        source: input.source,
        text: input.text,
        phone_number: input.phoneNumber || null,
        upi_id: input.upiId || null,
        url: input.url || null
      }

      response = await fetch(`${apiUrl}/fraud/analyze-text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload),
      })
    }

    onStateChange("classifying")
    await sleep(200)

    if (!response.ok) {
      throw new Error("Failed to analyze threat")
    }

    const json = await response.json()
    const verdict = json.data as ThreatVerdict

    onStateChange("recommending")
    await sleep(200)

    onStateChange("complete")
    return verdict
  } catch (error) {
    onStateChange("error")
    console.error("Analysis failed:", error)
    // Fallback to error state
    return {
      level: "Safe",
      score: 0,
      confidence: 0,
      category: "Unknown / Requires Review",
      assessment: "Analysis failed. Please check your backend connection.",
      evidence: [],
      entities: [],
      recommendations: ["Ensure the backend server is running."],
      timestamp: new Date().toISOString()
    }
  }
}
