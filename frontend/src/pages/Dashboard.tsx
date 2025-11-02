import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, DollarSign, FileCheck, Smartphone, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api';
import { formatXrp, formatRelativeTime, truncateHash, getExplorerLink } from '@/lib/utils';

export default function Dashboard() {
  const { data: receipts, isLoading: receiptsLoading } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => api.getReceipts(),
    refetchInterval: 10000,
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
  });

  // Calculate stats
  const stats = {
    totalSettled: receipts?.length || 0,
    totalRevenue: receipts?.reduce((sum, r) => sum + Number(r.amount_drops), 0) || 0,
    recentSettlements: receipts?.slice(-5).reverse() || [],
  };

  const statCards = [
    {
      name: 'Total Revenue',
      value: formatXrp(stats.totalRevenue, 2),
      icon: DollarSign,
      color: 'bg-green-500',
      trend: '+12.5%',
    },
    {
      name: 'Settled Claims',
      value: stats.totalSettled.toString(),
      icon: FileCheck,
      color: 'bg-blue-500',
      trend: '+5',
    },
    {
      name: 'Active Devices',
      value: '3',
      icon: Smartphone,
      color: 'bg-purple-500',
      trend: '+1',
    },
    {
      name: 'Success Rate',
      value: '98.5%',
      icon: TrendingUp,
      color: 'bg-orange-500',
      trend: '+2.1%',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Monitor your XRPL offline payment channels in real-time
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm font-medium text-green-600">{stat.trend}</span>
              </div>
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Settlements */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Settlements
          </h2>

          {receiptsLoading ? (
            <div className="flex justify-center py-8">
              <div className="loading-spinner"></div>
            </div>
          ) : stats.recentSettlements.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileCheck className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No settlements yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {stats.recentSettlements.map((receipt) => (
                <div
                  key={receipt.tx_hash}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-sm text-gray-900">
                        {truncateHash(receipt.tx_hash, 6, 6)}
                      </span>
                      <a
                        href={getExplorerLink(receipt.tx_hash, 'tx', 'testnet')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <ArrowUpRight className="w-4 h-4" />
                      </a>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatRelativeTime(receipt.settledAt)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">
                      {formatXrp(receipt.amount_drops, 2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System Health */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>

          {health ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div>
                  <p className="font-medium text-green-900">API Status</p>
                  <p className="text-sm text-green-700">All systems operational</p>
                </div>
                <div className="w-3 h-3 bg-green-500 rounded-full status-pulse"></div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Database</span>
                  <span
                    className={`badge ${
                      health.db === 'connected' ? 'badge-success' : 'badge-warning'
                    }`}
                  >
                    {health.db}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Settlement Mode</span>
                  <span
                    className={`badge ${
                      health.simulate_settlement ? 'badge-warning' : 'badge-success'
                    }`}
                  >
                    {health.submit_mode}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Exposure Cap</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formatXrp(health.exposure_cap_drops, 1)}
                  </span>
                </div>

                {health.merchant_address && (
                  <div className="pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">Merchant Address</p>
                    <p className="font-mono text-sm text-gray-900 break-all">
                      {health.merchant_address}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex justify-center py-8">
              <div className="loading-spinner"></div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-primary">Register New Device</button>
          <button className="btn-secondary">Process Claims</button>
          <button className="btn-secondary">View Analytics</button>
        </div>
      </div>
    </div>
  );
}
