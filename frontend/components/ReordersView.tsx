"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { Package, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { useState } from "react";

export function ReordersView() {
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["reorders"],
    queryFn: () => apiClient.getAllReorders(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const reorders = data || [];

  const statusFilters = [
    { value: "all", label: "All" },
    { value: "pending", label: "Pending" },
    { value: "processing", label: "Processing" },
    { value: "shipped", label: "Shipped" },
    { value: "delivered", label: "Delivered" },
  ];

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case "processing":
        return <Package className="h-4 w-4 text-blue-600" />;
      case "shipped":
        return <Package className="h-4 w-4 text-purple-600" />;
      case "delivered":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "processing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "shipped":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "delivered":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const filteredReorders = selectedStatus === "all" 
    ? reorders 
    : reorders.filter((r) => r.status === selectedStatus);

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

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">
          Error loading reorders: {error instanceof Error ? error.message : "Unknown error"}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Package className="h-5 w-5" />
            Reorders & Purchase Orders
          </h2>
        </div>

        {/* Status Filter */}
        <div className="flex gap-2 flex-wrap">
          {statusFilters.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setSelectedStatus(filter.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedStatus === filter.value
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {filteredReorders.length === 0 ? (
          <div className="text-center py-8">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No reorders found</p>
            <p className="text-xs text-gray-400 mt-1">
              Reorders will appear here once created
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredReorders.map((reorder) => (
              <div
                key={reorder.reorder_id || reorder.task_id || `reorder-${reorder.product_id}`}
                className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusIcon(reorder.status)}
                      <span className={`px-2 py-1 text-xs font-semibold rounded border ${getStatusColor(reorder.status)}`}>
                        {reorder.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="font-medium text-gray-900">
                      {reorder.product_name || "Product"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {reorder.quantity && `Quantity: ${reorder.quantity} • `}Order ID: {reorder.reorder_id ? reorder.reorder_id.slice(0, 8) : reorder.task_id ? reorder.task_id.slice(0, 8) : 'N/A'}
                    </p>
                    {reorder.purchase_order_id && (
                      <p className="text-xs text-gray-500 mt-1">
                        PO: {reorder.purchase_order_id}
                      </p>
                    )}
                    {reorder.eta && (
                      <p className="text-xs text-blue-600 mt-1">
                        ETA: {new Date(reorder.eta).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  {(reorder.created_at || reorder.assigned_date) && (
                    <div className="text-right">
                      <p className="text-xs text-gray-400">
                        {new Date(reorder.created_at || reorder.assigned_date || '').toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

