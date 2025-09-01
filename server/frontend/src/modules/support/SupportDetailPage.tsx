import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useMemo, useRef, useEffect } from 'react';
import { api } from '../../shared/api';

type SupportTicketOut = {
  id: string;
  user_id: string;
  subject: string;
  status: 'open' | 'pending' | 'closed' | 'rejected';
  created_at: string;
};

type SupportMessageOut = {
  id: string;
  ticket_id: string;
  author: 'user' | 'support';
  body: string;
  created_at: string;
};

export default function SupportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  // верхний вертикальный зазор между заголовком и первым блоком — 12px по стилям
  const topGap = 12;
  // желаемый небольшой зазор между списком сообщений и полем ввода
  const bottomGap = 8;
  // нижний отступ контента = высота композера + такой же зазор
  // removed composerPad: height is managed by flex layout now

  // если нет id в урле
  if (!id) {
    return (
      <div className="page-white">
        <div className="dashboard">
          <h1>Обращение</h1>
          <p>Некорректный адрес: нет id</p>
        </div>
      </div>
    );
  }

  const ticketQ = useQuery({
    queryKey: ['support', id],
    enabled: !!id,
    queryFn: async () => {
      const data = await api.get<SupportTicketOut>(`/api/v1/support/${id}`);
      return data;
    },
  });

  const msgsQ = useQuery({
    queryKey: ['support', id, 'messages'],
    enabled: !!id,
    queryFn: async () => {
      const data = await api.get<SupportMessageOut[]>(`/api/v1/support/${id}/messages`);
      return data;
    },
  });

  // current user to display proper author name
  const meQ = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<{ name?: string|null }>('/api/v1/user/me'),
  });

  const displayUserName = useMemo(() => {
    const raw = (meQ.data?.name || '').trim();
    if (!raw) return 'Я';
    const parts = raw.split(/\s+/);
    if (parts.length >= 2) {
      const [first, last] = [parts[0], parts[1]];
      return `${last} ${first}`; // Фамилия Имя
    }
    return raw;
  }, [meQ.data?.name]);

  // message composer
  const [text, setText] = useState('');
  const sendMutation = useMutation({
    mutationFn: async (body: string) => {
      return api.post(`/api/v1/support/${id}/messages/user`, { body });
    },
    onSuccess: () => {
      setText('');
      qc.invalidateQueries({ queryKey: ['support', id, 'messages'] });
    },
  });

  if (ticketQ.isLoading) {
    return (
      <div className="page-white">
        <div className="dashboard"><p>Загрузка…</p></div>
      </div>
    );
  }

  if (ticketQ.isError || !ticketQ.data) {
    return (
      <div className="page-white">
        <div className="dashboard">
          <p>Не удалось загрузить обращение.</p>
          <button className="btn btn-primary" onClick={() => navigate(-1)}>Назад</button>
        </div>
      </div>
    );
  }

  const t = ticketQ.data;
  const messages = msgsQ.data ?? [];

  const statusLabel: Record<SupportTicketOut['status'], string> = {
    open: 'Open',
    pending: 'Pending',
    closed: 'Closed',
    rejected: 'Rejected',
  }

  return (
    <div className="page-white">
      {/* Фиксированный экран: скролл отключён у страницы, только у блока сообщений */}
      <div className="dashboard" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <h1>Обращение</h1>

        {/* 1) Общая информация — закреплена (не прокручивается) */}
        <div className="summary-card" style={{ flex: '0 0 auto' }}>
          <div className="title" style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span>{t.subject}</span>
            <span className={`req-badge st-${t.status}`}>{statusLabel[t.status]}</span>
          </div>
          <div className="meta">создано: {new Date(t.created_at).toLocaleString('ru-RU')}</div>
        </div>

        <MessagesBox
          loading={msgsQ.isLoading}
          items={messages}
          displayUserName={displayUserName}
        />
      </div>

      {/* 3) Поле ввода — фиксировано над нижним меню */}
      <SupportComposer
        value={text}
        onChange={setText}
        onSend={() => sendMutation.mutate(text.trim())}
        sending={sendMutation.isPending}
        gap={topGap}
        bottomGap={bottomGap}
        // height is handled by flex; no need to notify parent
      />
    </div>
  );
}

function MessagesBox({ loading, items, displayUserName }: { loading: boolean; items: SupportMessageOut[]; displayUserName: string }) {
  const boxRef = useRef<HTMLDivElement | null>(null)
  

  useEffect(() => {
    const el = boxRef.current
    if (!el) return
    // скроллим к последнему сообщению
    el.scrollTop = el.scrollHeight
  }, [items.length])

  return (
    <div className="summary-card" style={{ flex: '1 1 auto', minHeight: 0, marginTop: 8, display: 'flex', flexDirection: 'column' }}>
      <div ref={boxRef} style={{ flex: '1 1 auto', minHeight: 0, overflowY: 'auto', overscrollBehavior: 'contain', paddingRight: 8 }}>
        {loading && <div className="meta">Загрузка…</div>}
        {!loading && items.length === 0 && (
          <div className="meta">Пока нет сообщений</div>
        )}
          {!loading && items.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 16, listStyle: 'none' }}>
              {items.map(m => (
                <li key={m.id} style={{ marginBottom: 8 }}>
                  <div className="meta">
                    {m.author === 'user' ? displayUserName : 'Поддержка'} {new Date(m.created_at).toLocaleString('ru-RU')}
                  </div>
                  <div className="support-msg-body">{m.body}</div>
                </li>
              ))}
            </ul>
          )}
      </div>
    </div>
  )
}

function SupportComposer({ value, onChange, onSend, sending, gap = 12, bottomGap = 8, onHeightChange }: { value: string; onChange: (v: string) => void; onSend: () => void; sending: boolean, gap?: number, bottomGap?: number, onHeightChange?: (h: number) => void }) {
  const ref = useRef<HTMLTextAreaElement | null>(null)

  // визуальные константы (должны совпадать со стилями ниже)
  const line = 20  // px
  const padV = 8   // px (сверху/снизу)
  const baseH = line + padV * 2
  const maxH = line * 5 + padV * 2
  const btnFixed = baseH // кнопка по высоте как одна строка ввода

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    const scrollH = Math.min(el.scrollHeight, maxH)
    el.style.height = Math.max(scrollH, baseH) + 'px'
    // Сообщим родителю полную высоту композера + маленький зазор до списка
    const h = Math.max(el.offsetHeight || baseH, btnFixed)
    onHeightChange?.(h + bottomGap)
  }, [value])

  return (
    <div style={{
      position: 'fixed',
      left: 0,
      right: 0,
      bottom: `calc(var(--nav-h) + env(safe-area-inset-bottom) + ${gap}px)`,
      zIndex: 1001,
    }}>
      <div style={{
        width: '100%',
        maxWidth: 'var(--content-max)',
        margin: '0 auto',
        padding: '0 12px',
        boxSizing: 'border-box',
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <textarea
            ref={ref}
            placeholder="Напишите сообщение"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={1}
            style={{
              flex: 1,
              resize: 'none',
              overflowY: 'hidden',
              minHeight: baseH,
              maxHeight: maxH,
              padding: `${padV}px 12px`,
              borderRadius: 12,
              border: '1px solid var(--border)',
              fontSize: 14,
              color: '#111827',
              lineHeight: `${line}px`,
              boxSizing: 'border-box',
              background: '#fff',
              outline: 'none',
            } as React.CSSProperties}
          />
          <button
            onClick={onSend}
            disabled={sending || !value.trim()}
            title="Отправить"
            aria-label="Отправить"
            style={{
              width: btnFixed,
              height: btnFixed,
              borderRadius: '50%',
              border: 0,
              background: 'var(--accent, #62B7FF)',
              color: '#0b0c10',
              fontWeight: 700,
              cursor: sending || !value.trim() ? 'default' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              textDecoration: 'none',
            }}
          >
            <span style={{ fontSize: 16, lineHeight: 1, transform: 'translateY(-1px)', textDecoration: 'none' }}>↑</span>
          </button>
        </div>
      </div>
    </div>
  )
}
