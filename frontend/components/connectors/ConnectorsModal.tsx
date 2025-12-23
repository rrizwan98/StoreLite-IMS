/**
 * ConnectorsModal Component
 *
 * Modal for managing MCP connectors - viewing list or adding new.
 */

'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import AppsToolsPanel from './AppsToolsPanel';
import AddConnectorForm from './AddConnectorForm';
import { Connector } from '@/lib/connectors-api';
import { SystemTool } from '@/lib/tools-api';

type ModalView = 'list' | 'add' | 'edit';

interface ConnectorsModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'system' | 'connectors';
  onToolSelect?: (tool: SystemTool) => void;
  onConnectorSelect?: (connector: Connector) => void;
}

export default function ConnectorsModal({
  isOpen,
  onClose,
  defaultTab = 'connectors',
  onToolSelect,
  onConnectorSelect,
}: ConnectorsModalProps) {
  const [view, setView] = useState<ModalView>('list');
  const [editConnector, setEditConnector] = useState<Connector | null>(null);

  // Reset view when modal opens
  useEffect(() => {
    if (isOpen) {
      setView('list');
      setEditConnector(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  function handleAddConnector() {
    setView('add');
  }

  function handleEditConnector(connector: Connector) {
    setEditConnector(connector);
    setView('edit');
  }

  function handleConnectorSuccess() {
    setView('list');
    setEditConnector(null);
  }

  function handleCancel() {
    setView('list');
    setEditConnector(null);
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-2xl md:max-h-[80vh] bg-white rounded-xl shadow-xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            {view === 'list' && 'Apps & Tools'}
            {view === 'add' && 'Add Connector'}
            {view === 'edit' && 'Edit Connector'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {view === 'list' && (
            <AppsToolsPanel
              defaultTab={defaultTab}
              onSystemToolClick={onToolSelect}
              onConnectorClick={onConnectorSelect}
              onAddConnector={handleAddConnector}
              onEditConnector={handleEditConnector}
            />
          )}

          {view === 'add' && (
            <div className="p-6">
              <AddConnectorForm
                onSuccess={handleConnectorSuccess}
                onCancel={handleCancel}
              />
            </div>
          )}

          {view === 'edit' && editConnector && (
            <div className="p-6">
              <EditConnectorView
                connector={editConnector}
                onSuccess={handleConnectorSuccess}
                onCancel={handleCancel}
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/**
 * Edit Connector View - Placeholder for editing existing connectors
 */
interface EditConnectorViewProps {
  connector: Connector;
  onSuccess: () => void;
  onCancel: () => void;
}

function EditConnectorView({ connector, onSuccess, onCancel }: EditConnectorViewProps) {
  const [name, setName] = useState(connector.name);
  const [description, setDescription] = useState(connector.description || '');
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // TODO: Implement update logic
    setSaving(true);
    try {
      const { updateConnector } = await import('@/lib/connectors-api');
      await updateConnector(connector.id, { name, description });
      onSuccess();
    } catch (err) {
      console.error('Failed to update connector:', err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Connector Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 hover:text-gray-900"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}
