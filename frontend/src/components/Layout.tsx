import { Outlet, Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Smartphone,
  FileText,
  Receipt,
  Settings,
  Activity,
} from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Devices', href: '/devices', icon: Smartphone },
  { name: 'Claims', href: '/claims', icon: FileText },
  { name: 'Receipts', href: '/receipts', icon: Receipt },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Layout() {
  const location = useLocation();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30000,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">X</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">XcceptaPay</h1>
                <p className="text-xs text-gray-500">XRPL Offline Payments</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Health Status */}
              <div className="flex items-center space-x-2">
                <Activity
                  className={cn(
                    'w-5 h-5',
                    health?.ok ? 'text-green-500 status-pulse' : 'text-red-500'
                  )}
                />
                <span className="text-sm text-gray-600">
                  {health?.ok ? 'Connected' : 'Offline'}
                </span>
              </div>

              {/* Merchant Address */}
              {health?.merchant_address && (
                <div className="hidden md:block">
                  <div className="text-xs text-gray-500">Merchant</div>
                  <div className="text-sm font-mono text-gray-700">
                    {health.merchant_address.slice(0, 10)}...
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-4rem)] sticky top-16">
          <nav className="p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-50'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* System Info */}
          {health && (
            <div className="p-4 mt-8 border-t border-gray-200">
              <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">
                System Status
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Database</span>
                  <span
                    className={cn(
                      'font-medium',
                      health.db === 'connected' ? 'text-green-600' : 'text-yellow-600'
                    )}
                  >
                    {health.db}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Mode</span>
                  <span className="font-medium text-gray-900">
                    {health.simulate_settlement ? 'Simulated' : 'Live'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Network</span>
                  <span className="font-medium text-gray-900">Testnet</span>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
