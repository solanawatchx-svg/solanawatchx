import { useEffect, useMemo, useState } from 'react';

type Token = {
  mint_address: string;
  creator_wallet: string;
  creation_ts: number;
  cts?: number;
  tvs?: number;
  chs?: number;
  sws?: number;
};

type TokensResponse = {
  items: Token[];
  total: number;
  page: number;
  page_size: number;
};

export default function TokensPage() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [minSws, setMinSws] = useState<number | ''>('');
  const [sort, setSort] = useState('-id');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  const params = useMemo(() => {
    const p = new URLSearchParams();
    if (q) p.set('q', q);
    if (minSws !== '') p.set('min_sws', String(minSws));
    if (sort) p.set('sort', sort);
    p.set('page', String(page));
    p.set('page_size', String(pageSize));
    return p.toString();
  }, [q, minSws, sort, page, pageSize]);

  const loadTokens = () => {
    fetch(`${apiBase}/tokens?${params}`)
      .then(r => r.json())
      .then((res: TokensResponse) => { setTokens(res.items || []); setTotal(res.total || 0); })
      .catch(() => {});
  };

  useEffect(() => { loadTokens(); }, [params]);

  return (
    <main style={{ padding: 24 }}>
      <h2>Tokens</h2>
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <input placeholder="Search mint/creator" value={q} onChange={e => { setPage(1); setQ(e.target.value); }} />
        <input placeholder="Min SWS" value={minSws} onChange={e => { setPage(1); const v = e.target.value; setMinSws(v === '' ? '' : Number(v)); }} style={{ width: 80 }} />
        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="-id">Newest</option>
          <option value="-sws">SWS desc</option>
          <option value="sws">SWS asc</option>
          <option value="-creation_ts">Newest by age</option>
          <option value="creation_ts">Oldest by age</option>
        </select>
        <select value={pageSize} onChange={e => { setPage(1); setPageSize(Number(e.target.value)); }}>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
        <button onClick={loadTokens}>Refresh</button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Mint</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Creator</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>Age</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>CTS</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>TVS</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>CHS</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}>SWS</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((t) => (
            <tr key={t.mint_address}>
              <td style={{ padding: '8px 4px' }}>{t.mint_address}</td>
              <td style={{ padding: '8px 4px' }}>{t.creator_wallet}</td>
              <td style={{ padding: '8px 4px' }}>{Math.max(0, Math.floor((Date.now()/1000 - (t.creation_ts||0))/60))} min</td>
              <td style={{ padding: '8px 4px' }}>{t.cts ?? '-'}</td>
              <td style={{ padding: '8px 4px' }}>{t.tvs ?? '-'}</td>
              <td style={{ padding: '8px 4px' }}>{t.chs ?? '-'}</td>
              <td style={{ padding: '8px 4px' }}>{t.sws ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
        <button disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</button>
        <span>Page {page} of {Math.max(1, Math.ceil(total / pageSize))}</span>
        <button disabled={page >= Math.ceil(total / pageSize)} onClick={() => setPage(p => p + 1)}>Next</button>
      </div>
    </main>
  );
}
