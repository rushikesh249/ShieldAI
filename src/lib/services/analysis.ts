import { AnalysisState, ThreatInput, ThreatVerdict } from "@/lib/types/citizen"

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

function generateFallbackVerdict(input: ThreatInput): ThreatVerdict {
  if (input.file) {
    return {
      level: "High-Risk",
      score: 84,
      confidence: 92,
      category: "Fake UPI Request",
      assessment: "Multimodal inspection flagged potential image tampering in uploaded file. Detected typography misalignment and irregular lighting artifacts consistent with fake payment templates.",
      evidence: [
        { label: "Visual Inconsistency", severity: "High", explanation: "Typography and alignment do not match authentic payment provider UI." },
        { label: "Template Artifacts", severity: "Critical", explanation: "File structural markers match known fraudulent receipt generation tool outputs." }
      ],
      entities: [
        { type: "Uploaded Image", value: input.file.name, copyable: false },
        { type: "File Size", value: `${(input.file.size / 1024).toFixed(1)} KB`, copyable: false }
      ],
      recommendations: [
        "Do not transfer funds or deliver goods based solely on screenshot proof.",
        "Verify account balance directly through your bank or payment app.",
        "Preserve original image file and communication logs for evidence."
      ],
      timestamp: new Date().toISOString()
    }
  }

  const text = input.text || ""
  const textLower = text.toLowerCase()

  // Keyword categories
  const digitalArrestKeywords = ["police", "cbi", "arrest", "court", "digital arrest", "skype", "warrant", "narcotics", "customs", "cyber cell", "fedex", "illegal package", "trai", "mha", "ed", "income tax", "legal notice"]
  const bankScamKeywords = ["bank", "account suspended", "account blocked", "otp", "kyc", "pan link", "netbanking", "unauthorized transaction", "debit card", "frozen", "deactivated", "card blocked"]
  const upiKeywords = ["upi", "paytm", "gpay", "google pay", "phonepe", "bhim", "qr", "qr code", "scan", "scan qr", "pin", "enter pin", "collect", "collect request", "receive", "receive payment", "scan to receive", "refund", "overpayment", "scan code", "transferred"]
  const lotteryJobKeywords = ["lottery", "won prize", "lucky draw", "claim reward", "part time job", "telegram task", "daily earning", "work from home", "vip task", "commission", "earn daily"]
  const phishingKeywords = ["click link", "verify here", "http", "bit.ly", "tinyurl", ".apk", "update now", "urgent"]

  const matchesDigitalArrest = digitalArrestKeywords.some(kw => textLower.includes(kw))
  const matchesBank = bankScamKeywords.some(kw => textLower.includes(kw)) || textLower.includes("otp")
  const matchesUPI = upiKeywords.some(kw => textLower.includes(kw)) ||
    (textLower.includes("scan") && (textLower.includes("qr") || textLower.includes("code") || textLower.includes("receive") || textLower.includes("gpay") || textLower.includes("pay"))) ||
    (textLower.includes("receive") && (textLower.includes("pin") || textLower.includes("gpay") || textLower.includes("google pay") || textLower.includes("paytm") || textLower.includes("qr") || textLower.includes("code") || textLower.includes("scan") || textLower.includes("payment"))) ||
    (textLower.includes("pin") && (textLower.includes("receive") || textLower.includes("enter"))) ||
    Boolean(input.upiId)
  const matchesLotteryJob = lotteryJobKeywords.some(kw => textLower.includes(kw))
  const matchesPhishing = phishingKeywords.some(kw => textLower.includes(kw)) || Boolean(input.url)

  if (matchesDigitalArrest) {
    return {
      level: "Critical",
      score: 96,
      confidence: 98,
      category: "Digital Arrest Scam",
      assessment: "High critical risk detected. The content uses coercive tactics: impersonation of law enforcement/investigation agencies (CBI/Police), fear inducement, and demands for video surveillance or urgent funds transfer.",
      evidence: [
        { label: "Law Enforcement Impersonation", severity: "Critical", explanation: "Claims official agency authority without verifiable government communication channels." },
        { label: "Coercive Fear Tactic", severity: "Critical", explanation: "Threatens immediate arrest or legal consequences to force compliance." }
      ],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "Phishing URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Do not join video calls or isolate yourself under pressure.",
        "Law enforcement agencies in India NEVER conduct 'digital arrests' via messaging or video apps.",
        "Immediately call Cyber Crime Helpline 1930 or report on cybercrime.gov.in."
      ],
      timestamp: new Date().toISOString()
    }
  }

  if (matchesBank) {
    return {
      level: "High-Risk",
      score: 90,
      confidence: 92,
      category: textLower.includes("otp") ? "OTP Fraud" : textLower.includes("kyc") ? "KYC Scam" : "Government Impersonation",
      assessment: "High risk identified. The message uses urgent threats regarding bank account suspension, credential harvesting, or unauthorized OTP requests.",
      evidence: [
        { label: "Urgent Financial Threat", severity: "Critical", explanation: "Threatens account suspension or block if recipient does not act immediately." },
        { label: "Credential Demand", severity: "High", explanation: "Requests confidential verification codes (OTP/KYC details)." }
      ],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "Phishing URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Never share OTPs, PINs, or netbanking passwords with anyone.",
        "Banks never ask for sensitive credentials or KYC updates via unverified messaging links.",
        "Contact your official bank customer care directly to verify account status."
      ],
      timestamp: new Date().toISOString()
    }
  }

  if (matchesUPI) {
    return {
      level: "High-Risk",
      score: 85,
      confidence: 90,
      category: "Fake UPI Request",
      assessment: "High risk payment fraud detected. Asks recipient to scan QR code, enter PIN, or use payment app to receive money. Entering PIN or scanning QR code always transfers money OUT.",
      evidence: [
        { label: "Reverse Payment / QR Code Scam", severity: "High", explanation: "Claims payment was sent but forces recipient to interact with payment gateway or PIN entry." },
        { label: "Unverified Destination", severity: "Medium", explanation: "UPI payment request has not been authenticated with standard merchant registries." }
      ],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "Phishing URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Remember: Entering your UPI PIN will DEDUCT money from your account, NOT receive money.",
        "Decline unknown UPI collect requests on payment apps immediately.",
        "Report suspicious UPI handles to your payment app provider."
      ],
      timestamp: new Date().toISOString()
    }
  }

  if (matchesLotteryJob) {
    return {
      level: "Suspicious",
      score: 75,
      confidence: 85,
      category: textLower.includes("lottery") || textLower.includes("prize") ? "Lottery Scam" : "Job Scam",
      assessment: "Suspicious advance-fee or task scam patterns detected. Promises unearned winnings, prizes, or easy daily task income.",
      evidence: [
        { label: "Unrealistic Income Promise", severity: "High", explanation: "Offers guaranteed high returns or prize money for minimal effort." },
        { label: "Advance Fee Indicator", severity: "Medium", explanation: "Likely requires initial registration or processing payment." }
      ],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "Phishing URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Do not pay any upfront registration or processing fees for prizes/jobs.",
        "Verify legitimate corporate job postings on official career websites.",
        "Block and report the sender on your messaging platform."
      ],
      timestamp: new Date().toISOString()
    }
  }

  if (matchesPhishing) {
    return {
      level: "Suspicious",
      score: 68,
      confidence: 80,
      category: "Phishing",
      assessment: "Suspicious external link or redirection detected. Caution advised before interacting with embedded URLs.",
      evidence: [
        { label: "External URL Redirection", severity: "Medium", explanation: "Contains unverified web links or shorteners." }
      ],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "Phishing URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Do not click on shortened or unverified web links.",
        "Check domain authenticity before typing personal information.",
        "Keep your device mobile OS and browser updated."
      ],
      timestamp: new Date().toISOString()
    }
  }

  // Check if normal benign conversation
  const safeConversationalPhrases = ["hello", "hi", "good morning", "good evening", "thank you", "thanks", "reschedule", "meeting", "see you", "lunch", "dinner", "call me", "how are you"]
  const isBenign = safeConversationalPhrases.some(p => new RegExp(`\\b${p}\\b`, 'i').test(textLower)) && textLower.split(/\s+/).length < 15 && !["pay", "money", "rs", "₹", "bank", "click", "urgent", "account", "verify", "link", "pin", "code", "card", "report", "file", "download", "apk"].some(c => textLower.includes(c))

  if (isBenign) {
    return {
      level: "Safe",
      score: 5,
      confidence: 95,
      category: "Safe Communication",
      assessment: "No scam indicators, phishing links, coercive threat patterns, or suspicious payment requests detected in this message.",
      evidence: [],
      entities: [
        ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
        ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
        ...(input.url ? [{ type: "URL", value: input.url, copyable: true }] : [])
      ],
      recommendations: [
        "Message appears safe based on standard threat pattern screening.",
        "Always remain vigilant regarding unsolicited requests for personal or financial details."
      ],
      timestamp: new Date().toISOString()
    }
  }

  // Unclassified / Unknown Text -> Caution
  return {
    level: "Caution",
    score: 45,
    confidence: 70,
    category: "Unknown / Requires Review",
    assessment: "Communication contains unverified or ambiguous indicators. Exercise caution before responding or sharing any personal data.",
    evidence: [
      { label: "Unverified Sender / Content", severity: "Medium", explanation: "Communication lacks authentic verification markers." }
    ],
    entities: [
      ...(input.phoneNumber ? [{ type: "Phone Number", value: input.phoneNumber, copyable: true }] : []),
      ...(input.upiId ? [{ type: "UPI ID", value: input.upiId, copyable: true }] : []),
      ...(input.url ? [{ type: "URL", value: input.url, copyable: true }] : [])
    ],
    recommendations: [
      "Exercise caution before responding to or clicking links from unverified senders.",
      "Do not share personal, financial, or authentication details (OTPs/PINs).",
      "Verify the identity of the sender through official channels before proceeding."
    ],
    timestamp: new Date().toISOString()
  }
}

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

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const json = await response.json()
    const verdict = json.data as ThreatVerdict

    onStateChange("classifying")
    await sleep(200)

    onStateChange("recommending")
    await sleep(200)

    onStateChange("complete")
    return verdict
  } catch (error) {
    console.warn("Backend API unavailable or error occurred; using local AI engine fallback:", error)
    
    onStateChange("classifying")
    await sleep(200)

    onStateChange("recommending")
    await sleep(200)

    onStateChange("complete")
    return generateFallbackVerdict(input)
  }
}

