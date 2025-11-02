import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Smartphone } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { formatXrp } from '@/lib/utils';

export default function Devices() {
  const queryClient = useQueryClient();
  const [deviceId, setDeviceId] = useState('');
  const [exposureCap, setExposureCap] = useState('3000000');
  const [registeredDevices, setRegisteredDevices] = useState<any[]>([]);

  const registerMutation = useMutation({
    mutationFn: ({ device_id, exposure_cap_drops }: any) =>
      api.registerDevice(device_id, exposure_cap_drops),
    onSuccess: (data) => {
      toast.success(`Device ${data.device_id} registered with tag ${data.dest_tag}`);
      setRegisteredDevices((prev) => [...prev, data]);
      setDeviceId('');
      setExposureCap('3000000');
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to register device');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceId.trim()) {
      toast.error('Device ID is required');
      return;
    }
    registerMutation.mutate({
      device_id: deviceId.trim(),
      exposure_cap_drops: Number(exposureCap),
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Devices</h1>
        <p className="text-gray-600 mt-1">
          Manage your POS devices and vending machines
        </p>
      </div>

      {/* Register New Device */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Plus className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">Register New Device</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Device ID
              </label>
              <input
                type="text"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                placeholder="e.g., vending-001"
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exposure Cap (drops)
              </label>
              <input
                type="number"
                value={exposureCap}
                onChange={(e) => setExposureCap(e.target.value)}
                placeholder="3000000"
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">
                {formatXrp(exposureCap)} maximum unsettled
              </p>
            </div>
          </div>

          <button
            type="submit"
            disabled={registerMutation.isPending}
            className="btn-primary"
          >
            {registerMutation.isPending ? 'Registering...' : 'Register Device'}
          </button>
        </form>
      </div>

      {/* Registered Devices */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Registered Devices ({registeredDevices.length})
        </h2>

        {registeredDevices.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Smartphone className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg">No devices registered yet</p>
            <p className="text-sm mt-2">Register your first device above</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Device ID
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Destination Tag
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Exposure Cap
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {registeredDevices.map((device) => (
                  <tr key={device.device_id} className="border-b border-gray-100">
                    <td className="py-4 px-4">
                      <span className="font-mono text-sm">{device.device_id}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="badge badge-info">{device.dest_tag}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-sm text-gray-700">
                        {formatXrp(device.exposure_cap_drops, 1)}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="badge badge-success">Active</span>
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
