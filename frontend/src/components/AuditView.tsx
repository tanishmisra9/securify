import { useEffect, useState } from 'react';

import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';

import { fetchAudit } from '../api/client';
import type { AuditRow } from '../types';
import VerdictBadge from './ui/VerdictBadge';

export default function AuditView() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setRows(await fetchAudit());
    } catch {
      // keep existing rows on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="h-full flex flex-col px-8 py-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <p className="section-label">Query Audit Log</p>
        <button onClick={() => void load()} className="text-t3 hover:text-t1 transition-colors" title="Refresh">
          <RefreshCw size={13} />
        </button>
      </div>

      <div className="flex-1 border border-border rounded-xl overflow-hidden min-h-0">
        <div className="h-full overflow-y-auto">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 bg-surface border-b border-border z-10">
              <tr>
                {['Timestamp', 'Query', 'Entities', 'Verdict', 'Injection'].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-[0.63rem] font-semibold uppercase tracking-[0.08em] text-t3 font-sans"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-t3 text-sm">
                    Loading…
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-t3 text-sm">
                    No queries logged yet.
                  </td>
                </tr>
              ) : (
                rows.map((row, i) => (
                  <motion.tr
                    key={row.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className={[
                      'border-b border-border last:border-0 transition-colors',
                      row.verdict === 'PASS'
                        ? 'bg-success/[0.03] hover:bg-success/[0.06]'
                        : 'bg-danger/[0.04] hover:bg-danger/[0.07]',
                    ].join(' ')}
                  >
                    <td className="px-4 py-3 font-mono text-[0.67rem] text-t3 whitespace-nowrap">
                      {row.timestamp.slice(0, 19).replace('T', ' ')}
                    </td>
                    <td className="px-4 py-3 text-[0.82rem] text-t1 max-w-[260px]">
                      <span className="line-clamp-2">
                        {row.query.length > 90 ? `${row.query.slice(0, 87)}…` : row.query}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[0.67rem] text-t3">
                      {row.entity_types.join(', ') || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <VerdictBadge verdict={row.verdict} />
                    </td>
                    <td className="px-4 py-3 text-center font-mono text-[0.67rem]">
                      {row.injection_attempt ? <span className="text-danger">Yes</span> : <span className="text-t3">—</span>}
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
