/**
 * OAuthConfirmModal Component
 *
 * Permission confirmation modal shown before OAuth redirect.
 * Similar to ChatGPT's connector permission dialog.
 */

'use client';

import Image from 'next/image';
import { X, Shield, Settings, AlertTriangle, ArrowRight } from 'lucide-react';
import { PredefinedConnector, getOAuthPermissionPoints } from '@/lib/predefined-connectors';

interface OAuthConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  connector: PredefinedConnector;
  isLoading?: boolean;
}

export default function OAuthConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  connector,
  isLoading = false,
}: OAuthConfirmModalProps) {
  if (!isOpen) return null;

  const permissionPoints = getOAuthPermissionPoints(connector.id);

  // Map icon string to component
  const getIcon = (iconType: 'shield' | 'control' | 'warning') => {
    switch (iconType) {
      case 'shield':
        return <Shield className="h-5 w-5 text-green-600" />;
      case 'control':
        return <Settings className="h-5 w-5 text-blue-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-600" />;
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-2xl shadow-2xl z-50 overflow-hidden">
        {/* Header with logos */}
        <div className="relative bg-gradient-to-b from-gray-50 to-white px-6 pt-6 pb-4">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>

          {/* Logos */}
          <div className="flex items-center justify-center space-x-4 mb-4">
            {/* IMS Logo */}
            <div className="w-14 h-14 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">IMS</span>
            </div>

            {/* Connection arrow */}
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <ArrowRight className="h-4 w-4 text-gray-400" />
            </div>

            {/* Connector Logo */}
            <div className="w-14 h-14 rounded-xl bg-white border border-gray-200 flex items-center justify-center shadow-lg overflow-hidden">
              <Image
                src={connector.logo}
                alt={connector.name}
                width={40}
                height={40}
                className="object-contain"
              />
            </div>
          </div>

          {/* Title */}
          <h2 className="text-xl font-semibold text-gray-900 text-center">
            Connect {connector.name}
          </h2>
          <p className="text-sm text-gray-500 text-center mt-1">
            Developed by {connector.developer}
          </p>
        </div>

        {/* Permission points */}
        <div className="px-6 py-4 space-y-4">
          {permissionPoints.map((point, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-0.5">
                {getIcon(point.icon)}
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900">{point.title}</h4>
                <p className="text-sm text-gray-600 mt-0.5">{point.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Footer with action button */}
        <div className="px-6 pb-6 pt-2">
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`
              w-full py-3 px-4 rounded-xl font-medium text-white transition-all
              flex items-center justify-center space-x-2
              ${isLoading
                ? 'bg-blue-400 cursor-wait'
                : 'bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl'
              }
            `}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <span>Continue to {connector.name}</span>
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>

          <p className="text-xs text-gray-500 text-center mt-3">
            You will be redirected to {connector.name} to authorize access
          </p>
        </div>
      </div>
    </>
  );
}
