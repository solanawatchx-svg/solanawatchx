import { useState } from 'react';

type TokenDetail = {
  mint_address: string;
  creator_wallet: string;
  creation_ts: number;
  cts?: number;
  tvs?: number;
  chs?: number;
  sws?: number;
  gini?: number;
  nakamoto?: number;
  chs_sources?: {
    has_twitter?: boolean;
    has_telegram?: boolean;
    domain_days?: number;
  };
};

export default function Admin() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const [mint, setMint] = useState('');
  const [detail, setDetail] = useState<TokenDetail | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${apiBase}/tokens/${mint}`);
      const j = await r.json();
      setDetail(j);
    } finally { setLoading(false); }
  };

  const refresh = async () => {
    setLoading(true);
    try {
      await fetch(`${apiBase}/tokens/${mint}/refresh`, { method: 'POST' });
      await load();
    } finally { setLoading(false); }
  };

  return (
    <main style={{ padding: 24 }}>
      <h2>Admin</h2>
      <div style={{ display: 'flex', gap: 8 }}>
        <input placeholder="Mint address" value={mint} onChange={e => setMint(e.target.value)} />
        <button onClick={load} disabled={!mint || loading}>Load</button>
        <button onClick={refresh} disabled={!mint || loading}>Refresh</button>
      </div>
      {detail && (
        <div style={{ marginTop: 16 }}>
          <div>Creator: {detail.creator_wallet}</div>
          <div>CTS: {detail.cts ?? '-'}</div>
          <div>TVS: {detail.tvs ?? '-'}</div>
          <div>CHS: {detail.chs ?? '-'}</div>
          <div>SWS: {detail.sws ?? '-'}</div>
          <div>Gini: {detail.gini ?? '-'}</div>
          <div>Nakamoto: {detail.nakamoto ?? '-'}</div>
          <div>
            CHS Sources: Twitter={String(detail.chs_sources?.has_twitter)}, Telegram={String(detail.chs_sources?.has_telegram)}, DomainDays={detail.chs_sources?.domain_days ?? '-'}
          </div>
          <div style={{ marginTop: 16 }}>
            <strong>Official Community</strong>
            <div><a href="https://discord.gg/GJbvD4CDmY" target="_blank" rel="noreferrer">Discord</a></div>
            <div><a href="https://x.com/solanawatchx" target="_blank" rel="noreferrer">X (Twitter)</a></div>
          </div>
        </div>
      )}
    </main>
  );
}
