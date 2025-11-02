import { useQuery } from '@tanstack/react-query';
import { Receipt as ReceiptIcon, ArrowUpRight, Download } from 'lucide-react';
import { api } from '@/lib/api';
import { formatXrp, formatDate, truncateHash, getExplorerLink } from '@/lib/utils';

export default function Receipts() {
  const { data: receipts, isLoading } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => api.getReceipts(),
    refetchInterval: 10000,
  });

  const totalRevenue = receipts?.reduce((sum, r) => sum + Number(r.amount_drops), 0) || 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Receipts</h1>
          <p className="text-gray-600 mt-1">
            View all settled PayChannel claims
          </p>
        </div>
        <button className="btn-secondary flex items-center space-x-2">
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Settlements</p>
          <p className="text-3xl font-bold text-gray-900">{receipts?.length || 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
          <p className="text-3xl font-bold text-green-600">
            {formatXrp(totalRevenue, 2)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600 mb-1">Average Settlement</p>
          <p className="text-3xl font-bold text-gray-900">
            {receipts && receipts.length > 0
              ? formatXrp(totalRevenue / receipts.length, 2)
              : '0 XRP'}
          </p>
        </div>
      </div>

      {/* Receipts Table */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">All Receipts</h2>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="loading-spinner"></div>
          </div>
        ) : !receipts || receipts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <ReceiptIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg">No receipts yet</p>
            <p className="text-sm mt-2">Settled claims will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Transaction Hash
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Channel ID
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Amount
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Ledger
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Settled At
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {receipts
                  .slice()
                  .reverse()
                  .map((receipt) => (
                    <tr
                      key={receipt.tx_hash}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-4 px-4">
                        <span className="font-mono text-sm text-gray-900">
                          {truncateHash(receipt.tx_hash, 8, 8)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-mono text-xs text-gray-600">
                          {truncateHash(receipt.channel_id, 6, 6)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-semibold text-green-600">
                          {formatXrp(receipt.amount_drops, 2)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="badge badge-info">{receipt.ledger_index}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-sm text-gray-600">
                          {formatDate(receipt.settledAt)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <a
                          href={getExplorerLink(receipt.tx_hash, 'tx', 'testnet')}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 inline-flex items-center space-x-1"
                        >
                          <span className="text-sm">View</span>
                          <ArrowUpRight className="w-4 h-4" />
                        </a>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
