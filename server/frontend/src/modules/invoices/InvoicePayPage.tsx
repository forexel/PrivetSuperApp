import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api'
import '../../styles/invoices.css'
import '../../styles/forms.css'

type Invoice = {
  id: string
  amount: number
  description?: string | null
  contract_number?: string | null
  due_date?: string | null
  status: string
}

export default function InvoicePayPage() {
  const nav = useNavigate()
  const [selected, setSelected] = useState<string[]>([])
  const [initialized, setInitialized] = useState(false)
  const [busy, setBusy] = useState(false)

  const { data: invoices = [], isLoading, isError } = useQuery({
    queryKey: ['invoices', 'my'],
    queryFn: () => api.get<Invoice[]>('/invoices/my'),
  })

  useEffect(() => {
    if (!initialized && invoices.length) {
      setSelected(invoices.map((inv) => inv.id))
      setInitialized(true)
    }
  }, [invoices, initialized])

  const total = useMemo(() => {
    return invoices
      .filter((inv) => selected.includes(inv.id))
      .reduce((sum, inv) => sum + (inv.amount || 0), 0)
  }, [invoices, selected])

  const toggle = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]))
  }

  const onPay = async () => {
    if (!selected.length) return
    try {
      setBusy(true)
      const resp = await api.post<{ redirect_url: string }>('/payments/yookassa/invoices', {
        invoice_ids: selected,
      })
      if (resp?.redirect_url) {
        window.location.assign(resp.redirect_url)
        return
      }
      throw new Error('redirect_url missing')
    } catch {
      nav('/invoices/denied', { replace: true })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page-blue page-blue--payment">
      <h1 className="auth-hero-title auth-hero-title--payment">Оплата</h1>
      <div className="modal-wrap modal-wrap--wide modal-wrap--no-close">
        <div className="card auth-card invoice-pay-card">
          <h1 className="card-title">Выберите счета</h1>

          {isLoading && <div className="invoice-empty">Загрузка счетов…</div>}
          {isError && <div className="invoice-empty">Не удалось загрузить счета</div>}

          {!isLoading && !isError && invoices.length === 0 && (
            <div className="invoice-empty">Нет счетов для оплаты</div>
          )}

          {!isLoading && !isError && invoices.length > 0 && (
            <>
              <div className="invoice-list">
                {invoices.map((inv) => (
                  <label key={inv.id} className="invoice-row">
                    <input
                      type="checkbox"
                      checked={selected.includes(inv.id)}
                      onChange={() => toggle(inv.id)}
                    />
                    <div className="invoice-main">
                      <div className="invoice-title">
                        Счёт {inv.contract_number ? `№${inv.contract_number}` : ''}
                      </div>
                      {inv.description && <div className="invoice-meta">{inv.description}</div>}
                      {inv.due_date && (
                        <div className="invoice-meta">
                          Оплатить до {new Date(inv.due_date).toLocaleDateString('ru-RU')}
                        </div>
                      )}
                      <div className="invoice-amount">{inv.amount.toLocaleString('ru-RU')} ₽</div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="invoice-total">Итого к оплате: {total.toLocaleString('ru-RU')} ₽</div>
            </>
          )}

          <button className="btn btn-primary" onClick={onPay} disabled={!selected.length || busy}>
            Перейти к оплате
          </button>
        </div>
      </div>
    </div>
  )
}
