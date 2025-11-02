import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Settings as SettingsIcon, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { QRCodeSVG } from 'qrcode.react';

export default function Settings() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
  });

  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || '/api');
  const [exposureCap, setExposureCap] = useState('3000000');

  const handleSave = () => {
    toast.success('Settings saved successfully');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure your payment system</p>
      </div>

      {/* API Configuration */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <SettingsIcon className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">API Configuration</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="input font-mono"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Exposure Cap (drops)
            </label>
            <input
              type="number"
              value={exposureCap}
              onChange={(e) => setExposureCap(e.target.value)}
              className="input"
            />
          </div>

          <button onClick={handleSave} className="btn-primary flex items-center space-x-2">
            <Save className="w-4 h-4" />
            <span>Save Settings</span>
          </button>
        </div>
      </div>

      {/* Merchant Info */}
      {health?.merchant_address && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Merchant Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Merchant Address
              </p>
              <p className="font-mono text-sm text-gray-900 bg-gray-50 p-3 rounded-lg break-all">
                {health.merchant_address}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Payment QR Code
              </p>
              <div className="bg-white p-4 rounded-lg border-2 border-gray-200 inline-block">
                <QRCodeSVG value={health.merchant_address} size={150} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Information */}
      {health && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            System Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Database Status</span>
              <span className="text-sm font-medium text-gray-900">{health.db}</span>
            </div>

            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Settlement Mode</span>
              <span className="text-sm font-medium text-gray-900">
                {health.submit_mode}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">RPC URL</span>
              <span className="text-sm font-mono text-gray-900">
                {health.rpc_url || 'Not configured'}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Exposure Cap</span>
              <span className="text-sm font-medium text-gray-900">
                {health.exposure_cap_drops} drops
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Auth Mode</span>
              <span className="text-sm font-medium text-gray-900">
                {health.dev_no_auth ? 'Development (No Auth)' : 'Production'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
