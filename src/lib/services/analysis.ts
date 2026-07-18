import { AnalysisState, ThreatInput, ThreatVerdict } from "@/lib/types/citizen"

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export async function analyzeThreat(
  input: ThreatInput,
  onStateChange: (state: AnalysisState) => void
): Promise<ThreatVerdict> {
  // Simulate API pipeline states
  onStateChange("validating")
  await sleep(600)
  
  onStateChange("extracting")
  await sleep(1200)
  
  onStateChange("analyzing")
  await sleep(1500)
  
  onStateChange("classifying")
  await sleep(1000)
  
  onStateChange("recommending")
  await sleep(800)

  // Determine mock response based on input content
  const text = input.text.toLowerCase()
  
  let verdict: ThreatVerdict = {
    level: "Safe",
    score: 12,
    confidence: 96,
    category: "Safe Communication",
    assessment: "This communication appears to be routine and safe. No deceptive language or urgent demands were detected.",
    evidence: [
      { label: "Standard phrasing", severity: "Informational", explanation: "Uses expected, safe communication patterns." }
    ],
    entities: [],
    recommendations: [
      "No special precautions needed.",
      "Always remain vigilant when sharing personal information."
    ],
    timestamp: new Date().toISOString()
  }

  // Keywords to simulate analysis logic
  if (text.includes("arrest") || text.includes("cbi") || text.includes("police") || text.includes("supreme court")) {
    verdict = {
      level: "Critical",
      score: 94,
      confidence: 88,
      category: "Digital Arrest Scam",
      assessment: "This communication contains multiple indicators commonly associated with digital-arrest impersonation scams, including fear-based language, false legal authority, urgency, and secrecy demands.",
      evidence: [
        { label: "Government/Police impersonation", severity: "Critical", explanation: "Claims authority to instil fear." },
        { label: "Threat of arrest", severity: "Critical", explanation: "Uses fake legal threats to force compliance." },
        { label: "Urgency and fear language", severity: "High", explanation: "Artificial urgency designed to bypass logical thinking." },
        { label: "Secrecy demand", severity: "High", explanation: "Instructs victim not to contact family or local police." }
      ],
      entities: [
        { type: "Claimed Authority", value: "CBI / Police", copyable: false }
      ],
      recommendations: [
        "Do not transfer any money.",
        "End this communication immediately.",
        "Preserve screenshots and records.",
        "Contact the national cybercrime reporting channel (1930) or local police."
      ],
      timestamp: new Date().toISOString()
    }
  } else if (text.includes("upi") || text.includes("otp") || text.includes("bank") || text.includes("blocked")) {
    verdict = {
      level: "High-Risk",
      score: 82,
      confidence: 91,
      category: "Phishing",
      assessment: "High risk of phishing or financial fraud. The sender is attempting to create urgency around your bank account or payment methods.",
      evidence: [
        { label: "Financial urgency", severity: "High", explanation: "Claims account is blocked or requires immediate action." },
        { label: "Credential request", severity: "Critical", explanation: "Asks for OTP, PIN, or sensitive banking details." },
        { label: "Suspicious link", severity: "High", explanation: "Contains an unverified URL for credential harvesting." }
      ],
      entities: [],
      recommendations: [
        "Do not click any links in the message.",
        "Do not share OTPs, PINs, or passwords with anyone.",
        "Verify your account status directly through your official banking app.",
        "Block the sender."
      ],
      timestamp: new Date().toISOString()
    }
  } else if (text.includes("lottery") || text.includes("prize") || text.includes("winner")) {
    verdict = {
      level: "Suspicious",
      score: 75,
      confidence: 85,
      category: "Lottery Scam",
      assessment: "The message follows common patterns of an advance-fee or lottery scam, promising unexpected wealth.",
      evidence: [
        { label: "Unexpected windfall", severity: "High", explanation: "Promises large sums of money without prior entry." },
        { label: "Advance fee demand", severity: "Medium", explanation: "May soon require a 'processing fee' to release funds." }
      ],
      entities: [],
      recommendations: [
        "Do not reply to the sender.",
        "Do not pay any processing fees or taxes upfront.",
        "Mark the communication as spam."
      ],
      timestamp: new Date().toISOString()
    }
  }

  // Add optional entities if provided in input
  if (input.phoneNumber) {
    verdict.entities.push({ type: "Phone Number", value: input.phoneNumber, copyable: true })
    if (verdict.level !== "Safe") {
      verdict.evidence.push({ label: "Unknown source", severity: "Medium", explanation: "Communication originated from an unverified number." })
    }
  }
  
  if (input.upiId) {
    verdict.entities.push({ type: "UPI ID", value: input.upiId, copyable: true })
    if (verdict.level !== "Safe") {
      verdict.evidence.push({ label: "Unverified UPI ID", severity: "High", explanation: "The payment receiver is not a verified merchant." })
    }
  }
  
  if (input.url) {
    verdict.entities.push({ type: "URL", value: input.url, copyable: true })
  }

  onStateChange("complete")
  return verdict
}
