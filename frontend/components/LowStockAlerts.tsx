"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { AlertTriangle } from "lucide-react";

export function LowStockAlerts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["inventory"],
    queryFn: () => apiClient.getAllProducts(),
    refetchInterval: 30000,
  });

  const lowStockItems = (data?.items || []).filter((p) => p.low_stock);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900">Low Stock Alerts</h2>
          {lowStockItems.length > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full">
              {lowStockItems.length}
            </span>
          )}
        </div>
      </div>

      <div className="p-6">
        {lowStockItems.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-green-500 mb-2">✓</div>
            <p className="text-sm text-gray-500">All products are well stocked!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {lowStockItems.slice(0, 10).map((product) => (
              <div
                key={product.product_id}
                className="p-3 border border-red-200 rounded-lg bg-red-50"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{product.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      SKU: {product.sku}
                      {product.color && ` • ${product.color}`}
                      {product.size && ` • ${product.size}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-red-600">
                      {product.quantity}
                    </p>
                    <p className="text-xs text-gray-500">
                      Threshold: {product.reorder_threshold}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            {lowStockItems.length > 10 && (
              <p className="text-xs text-gray-500 text-center">
                +{lowStockItems.length - 10} more items...
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

