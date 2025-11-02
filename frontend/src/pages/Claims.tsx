import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FileText, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { formatXrp, truncateHash } from '@/lib/utils';

export default function Claims() {
  const [claimJson, setClaimJson] = useState('');
  const [verificationResult, setVerificationResult] = useState<any>(null);

  const verifyMutation = useMutation({
    mutationFn: (claim: any) => api.verifyClaim(claim),
    onSuccess: (data) => {
      setVerificationResult(data);
      if (data.valid) {
        toast.success('Claim signature is valid!');
      } else {
        toast.error(`Verification failed: ${data.reason || 'Invalid signature'}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Verification failed');
    },
  });

  const queueMutation = useMutation({
    mutationFn: (claim: any) => api.queueClaim(claim),
    onSuccess: (data) => {
      if (data.accepted) {
        toast.success('Claim queued for settlement');
      } else {
        toast.error(`Queue failed: ${data.reason || 'Unknown error'}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.reason || 'Failed to queue claim');
    },
  });

  const settleMutation = useMutation({
    mutationFn: () => api.settleClaim(),
    onSuccess: (data) => {
      if (data.ok) {
        toast.success(
          `Settlement successful! TX: ${truncateHash(data.tx_hash || '', 6, 6)}`
        );
      } else {
        toast.error(`Settlement failed: ${data.reason || 'Unknown error'}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.reason || 'Settlement failed');
    },
  });

  const handleVerify = () => {
    try {
      const claim = JSON.parse(claimJson);
      verifyMutation.mutate(claim);
    } catch (e) {
      toast.error('Invalid JSON format');
    }
  };

  const handleQueue = () => {
    try {
      const claim = JSON.parse(claimJson);
      queueMutation.mutate(claim);
    } catch (e) {
      toast.error('Invalid JSON format');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Claims</h1>
        <p className="text-gray-600 mt-1">
          Verify and process PayChannel claims offline
        </p>
      </div>

      {/* Claim Input */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <FileText className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">Process Claim</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Claim JSON
            </label>
            <textarea
              value={claimJson}
              onChange={(e) => setClaimJson(e.target.value)}
              rows={8}
              placeholder={`{
  "channel_id": "...",
  "amount_drops": "2000000",
  "signature": "...",
  "pubkey": "..."
}`}
              className="input font-mono text-sm"
            />
            <p className="text-xs text-gray-500 mt-2">
              Paste the claim JSON received from the buyer's wallet
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleVerify}
              disabled={verifyMutation.isPending || !claimJson.trim()}
              className="btn-primary"
            >
              {verifyMutation.isPending ? 'Verifying...' : 'Verify Signature'}
            </button>
            <button
              onClick={handleQueue}
              disabled={queueMutation.isPending || !claimJson.trim()}
              className="btn-secondary"
            >
              {queueMutation.isPending ? 'Queueing...' : 'Queue for Settlement'}
            </button>
            <button
              onClick={() => settleMutation.mutate()}
              disabled={settleMutation.isPending}
              className="btn-success"
            >
              {settleMutation.isPending ? 'Settling...' : 'Settle Now'}
            </button>
          </div>
        </div>
      </div>

      {/* Verification Result */}
      {verificationResult && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Verification Result
          </h2>

          <div
            className={`p-4 rounded-lg border-2 ${
              verificationResult.valid
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              {verificationResult.valid ? (
                <CheckCircle className="w-8 h-8 text-green-600" />
              ) : (
                <XCircle className="w-8 h-8 text-red-600" />
              )}
              <div>
                <p
                  className={`font-semibold ${
                    verificationResult.valid ? 'text-green-900' : 'text-red-900'
                  }`}
                >
                  {verificationResult.valid
                    ? 'Signature Valid'
                    : 'Signature Invalid'}
                </p>
                {verificationResult.reason && (
                  <p
                    className={`text-sm ${
                      verificationResult.valid ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    Reason: {verificationResult.reason}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Example Claim */}
      <div className="card bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Example Claim Format
        </h3>
        <pre className="text-xs font-mono text-gray-600 overflow-x-auto">
          {JSON.stringify(
            {
              channel_id:
                'A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E9F0A1B2',
              amount_drops: '2000000',
              signature:
                '304502210...(128 hex chars)...9876543210',
              pubkey: 'ED01234567890ABCDEF...',
            },
            null,
            2
          )}
        </pre>
      </div>
    </div>
  );
}
