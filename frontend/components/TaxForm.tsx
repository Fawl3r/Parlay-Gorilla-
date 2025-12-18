"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, AlertCircle, CheckCircle, FileText, Loader2, Info } from "lucide-react"
import { api } from "@/lib/api"
import { toast } from "sonner"

interface TaxFormStatus {
  form_type: string | null
  form_status: string
  requires_form: boolean
  form_complete: boolean
  submitted_at: string | null
  verified_at: string | null
  threshold: number
  earnings: number
  masked_tax_id: string | null
}

interface TaxFormProps {
  onClose: () => void
  onSuccess?: () => void
}

export function TaxForm({ onClose, onSuccess }: TaxFormProps) {
  const [status, setStatus] = useState<TaxFormStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [formType, setFormType] = useState<"w9" | "w8ben" | null>(null)
  const [step, setStep] = useState<"select" | "form">("select")

  // W-9 Form fields
  const [w9Data, setW9Data] = useState({
    legal_name: "",
    business_name: "",
    tax_classification: "Individual" as "Individual" | "Partnership" | "C-Corp" | "S-Corp" | "LLC" | "Other",
    address_street: "",
    address_city: "",
    address_state: "",
    address_zip: "",
    address_country: "US",
    tax_id_number: "",
    tax_id_type: "ssn" as "ssn" | "ein",
  })

  // W-8BEN Form fields
  const [w8benData, setW8benData] = useState({
    legal_name: "",
    business_name: "",
    country_of_residence: "",
    foreign_tax_id: "",
    address_street: "",
    address_city: "",
    address_state: "",
    address_zip: "",
    address_country: "",
  })

  useEffect(() => {
    loadTaxStatus()
  }, [])

  const loadTaxStatus = async () => {
    try {
      setLoading(true)
      const data = await api.getTaxFormStatus()
      setStatus(data)
      if (data.form_type) {
        setFormType(data.form_type as "w9" | "w8ben")
        setStep("form")
      }
    } catch (error: any) {
      console.error("Failed to load tax status:", error)
      toast.error("Failed to load tax form status")
    } finally {
      setLoading(false)
    }
  }

  const handleW9Submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.submitW9TaxForm(w9Data)
      toast.success("Tax form submitted successfully! It will be reviewed and verified.")
      await loadTaxStatus()
      onSuccess?.()
      onClose()
    } catch (error: any) {
      console.error("Failed to submit W-9 form:", error)
      toast.error(error.response?.data?.detail || "Failed to submit tax form")
    } finally {
      setSubmitting(false)
    }
  }

  const handleW8BENSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.submitW8BENTaxForm(w8benData)
      toast.success("Tax form submitted successfully! It will be reviewed and verified.")
      await loadTaxStatus()
      onSuccess?.()
      onClose()
    } catch (error: any) {
      console.error("Failed to submit W-8BEN form:", error)
      toast.error(error.response?.data?.detail || "Failed to submit tax form")
    } finally {
      setSubmitting(false)
    }
  }

  const formatTaxId = (value: string) => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, "")
    if (w9Data.tax_id_type === "ssn") {
      // Format as XXX-XX-XXXX
      if (digits.length <= 3) return digits
      if (digits.length <= 5) return `${digits.slice(0, 3)}-${digits.slice(3)}`
      return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5, 9)}`
    } else {
      // Format EIN as XX-XXXXXXX
      if (digits.length <= 2) return digits
      return `${digits.slice(0, 2)}-${digits.slice(2, 9)}`
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="bg-[#0A0F0A] border border-emerald-500/30 rounded-xl p-8">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500 mx-auto" />
        </div>
      </div>
    )
  }

  if (status?.form_complete) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[#0A0F0A] border border-emerald-500/30 rounded-xl p-6 max-w-md w-full"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <CheckCircle className="h-6 w-6 text-emerald-400" />
              Tax Form Verified
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="text-gray-300 mb-4">
            Your {status.form_type?.toUpperCase()} tax form has been verified. You're all set!
          </p>
          {status.masked_tax_id && (
            <p className="text-sm text-gray-400">
              Tax ID: {status.masked_tax_id}
            </p>
          )}
          <button
            onClick={onClose}
            className="mt-4 w-full px-4 py-2 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
          >
            Close
          </button>
        </motion.div>
      </div>
    )
  }

  if (step === "select") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[#0A0F0A] border border-emerald-500/30 rounded-xl p-6 max-w-md w-full"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <FileText className="h-6 w-6 text-emerald-400" />
              Tax Form Required
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {status && (
            <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-yellow-400 mb-1">
                    Tax Form Required
                  </p>
                  <p className="text-sm text-gray-300">
                    You've earned ${status.earnings.toFixed(2)} in commissions. 
                    US law requires a tax form for earnings over ${status.threshold.toFixed(2)}.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={() => {
                setFormType("w9")
                setStep("form")
              }}
              className="w-full p-4 bg-white/5 border border-white/10 rounded-lg hover:border-emerald-500/50 hover:bg-white/10 transition-all text-left"
            >
              <div className="font-semibold text-white mb-1">W-9 Form (US Affiliates)</div>
              <div className="text-sm text-gray-400">For US citizens and residents</div>
            </button>
            <button
              onClick={() => {
                setFormType("w8ben")
                setStep("form")
              }}
              className="w-full p-4 bg-white/5 border border-white/10 rounded-lg hover:border-emerald-500/50 hover:bg-white/10 transition-all text-left"
            >
              <div className="font-semibold text-white mb-1">W-8BEN Form (International)</div>
              <div className="text-sm text-gray-400">For non-US affiliates</div>
            </button>
          </div>

          <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-blue-400 mt-0.5" />
              <p className="text-xs text-gray-400">
                Your tax information is encrypted and secure. We only use this for tax reporting purposes.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-[#0A0F0A] border border-emerald-500/30 rounded-xl p-6 max-w-2xl w-full my-8"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-emerald-400" />
            {formType === "w9" ? "W-9 Tax Form" : "W-8BEN Tax Form"}
          </h2>
          <button
            onClick={() => setStep("select")}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {formType === "w9" ? (
          <form onSubmit={handleW9Submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Legal Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w9Data.legal_name}
                onChange={(e) => setW9Data({ ...w9Data, legal_name: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Business Name (if applicable)
              </label>
              <input
                type="text"
                value={w9Data.business_name}
                onChange={(e) => setW9Data({ ...w9Data, business_name: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="ABC Company LLC"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Tax Classification <span className="text-red-400">*</span>
              </label>
              <select
                required
                value={w9Data.tax_classification}
                onChange={(e) => setW9Data({ ...w9Data, tax_classification: e.target.value as any })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
              >
                <option value="Individual">Individual</option>
                <option value="Partnership">Partnership</option>
                <option value="C-Corp">C-Corporation</option>
                <option value="S-Corp">S-Corporation</option>
                <option value="LLC">LLC</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Street Address <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w9Data.address_street}
                onChange={(e) => setW9Data({ ...w9Data, address_street: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="123 Main St"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  City <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={w9Data.address_city}
                  onChange={(e) => setW9Data({ ...w9Data, address_city: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                  placeholder="New York"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  State <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  maxLength={2}
                  value={w9Data.address_state}
                  onChange={(e) => setW9Data({ ...w9Data, address_state: e.target.value.toUpperCase() })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                  placeholder="NY"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                ZIP Code <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w9Data.address_zip}
                onChange={(e) => setW9Data({ ...w9Data, address_zip: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="10001"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Tax ID Type <span className="text-red-400">*</span>
              </label>
              <select
                required
                value={w9Data.tax_id_type}
                onChange={(e) => setW9Data({ ...w9Data, tax_id_type: e.target.value as "ssn" | "ein" })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
              >
                <option value="ssn">SSN (Social Security Number)</option>
                <option value="ein">EIN (Employer Identification Number)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {w9Data.tax_id_type === "ssn" ? "SSN" : "EIN"} <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={formatTaxId(w9Data.tax_id_number)}
                onChange={(e) => {
                  const digits = e.target.value.replace(/\D/g, "")
                  setW9Data({ ...w9Data, tax_id_number: digits })
                }}
                maxLength={w9Data.tax_id_type === "ssn" ? 11 : 10}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none font-mono"
                placeholder={w9Data.tax_id_type === "ssn" ? "XXX-XX-XXXX" : "XX-XXXXXXX"}
              />
            </div>

            <div className="pt-4 flex gap-3">
              <button
                type="button"
                onClick={() => setStep("select")}
                className="flex-1 px-4 py-2 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Form"
                )}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleW8BENSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Legal Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w8benData.legal_name}
                onChange={(e) => setW8benData({ ...w8benData, legal_name: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Business Name (if applicable)
              </label>
              <input
                type="text"
                value={w8benData.business_name}
                onChange={(e) => setW8benData({ ...w8benData, business_name: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Country of Residence <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w8benData.country_of_residence}
                onChange={(e) => setW8benData({ ...w8benData, country_of_residence: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                placeholder="Canada"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Foreign Tax ID (if applicable)
              </label>
              <input
                type="text"
                value={w8benData.foreign_tax_id}
                onChange={(e) => setW8benData({ ...w8benData, foreign_tax_id: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Street Address <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={w8benData.address_street}
                onChange={(e) => setW8benData({ ...w8benData, address_street: e.target.value })}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  City <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={w8benData.address_city}
                  onChange={(e) => setW8benData({ ...w8benData, address_city: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  State/Province
                </label>
                <input
                  type="text"
                  value={w8benData.address_state}
                  onChange={(e) => setW8benData({ ...w8benData, address_state: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  ZIP/Postal Code <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={w8benData.address_zip}
                  onChange={(e) => setW8benData({ ...w8benData, address_zip: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Country <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={w8benData.address_country}
                  onChange={(e) => setW8benData({ ...w8benData, address_country: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            <div className="pt-4 flex gap-3">
              <button
                type="button"
                onClick={() => setStep("select")}
                className="flex-1 px-4 py-2 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Form"
                )}
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  )
}




