import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api';

type SupportTicketOut = {
  id: string;
  user_id: string;
  subject: string;
  status: 'open' | 'in_progress' | 'closed' | 'rejected';
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

  return (
    <div className="page-white">
      <div className="dashboard">
        <h1>Обращение</h1>

        <div className="summary-card">
          <div className="title">{t.subject}</div>
          <div className="meta">
            статус: {t.status} · создано: {new Date(t.created_at).toLocaleString()}
          </div>
        </div>

        <div className="summary-card" style={{ marginTop: 8 }}>
          <div className="title">Сообщения</div>
          {msgsQ.isLoading && <div className="meta">Загрузка…</div>}
          {!msgsQ.isLoading && messages.length === 0 && (
            <div className="meta">Пока нет сообщений</div>
          )}
          {!msgsQ.isLoading && messages.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 16 }}>
              {messages.map(m => (
                <li key={m.id} style={{ marginBottom: 8 }}>
                  <div className="meta">
                    {m.author} · {new Date(m.created_at).toLocaleString()}
                  </div>
                  <div>{m.body}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}