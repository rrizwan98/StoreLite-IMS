/**
 * Item Actions Component
 * Reusable component for Edit/Delete actions on items
 * Used in ItemsTable for cleaner code organization
 */

'use client';

import { Item } from '@/lib/types';

export interface ItemActionsProps {
  item: Item;
  onEdit?: (item: Item) => void;
  onDelete?: (item: Item) => void;
  disabled?: boolean;
}

export default function ItemActions({
  item,
  onEdit,
  onDelete,
  disabled = false,
}: ItemActionsProps) {
  return (
    <div className="flex items-center justify-center gap-2">
      {onEdit && (
        <button
          onClick={() => onEdit(item)}
          disabled={disabled}
          className="px-3 py-1 bg-primary text-white text-xs font-medium rounded hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Edit
        </button>
      )}
      {onDelete && (
        <button
          onClick={() => {
            if (
              window.confirm(
                `Are you sure you want to delete "${item.name}"? This action cannot be undone.`
              )
            ) {
              onDelete(item);
            }
          }}
          disabled={disabled}
          className="px-3 py-1 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Delete
        </button>
      )}
    </div>
  );
}
