import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class AffiliateApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getTaxFormStatus() {
    const response = await this.clients.apiClient.get('/api/affiliates/me/tax-status')
    return response.data
  }

  async submitW9TaxForm(formData: {
    legal_name: string
    business_name?: string
    tax_classification: 'Individual' | 'Partnership' | 'C-Corp' | 'S-Corp' | 'LLC' | 'Other'
    address_street: string
    address_city: string
    address_state: string
    address_zip: string
    address_country?: string
    tax_id_number: string
    tax_id_type: 'ssn' | 'ein'
  }) {
    const response = await this.clients.apiClient.post('/api/affiliates/me/tax-form/w9', formData)
    return response.data
  }

  async submitW8BENTaxForm(formData: {
    legal_name: string
    business_name?: string
    country_of_residence: string
    foreign_tax_id?: string
    address_street: string
    address_city: string
    address_state?: string
    address_zip: string
    address_country: string
  }) {
    const response = await this.clients.apiClient.post('/api/affiliates/me/tax-form/w8ben', formData)
    return response.data
  }
}




