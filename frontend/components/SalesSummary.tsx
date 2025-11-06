"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, DollarSign, ShoppingCart } from "lucide-react";

export function SalesSummary() {
  const [windowDays, setWindowDays] = useState(7);

  const { data: summary7, isLoading: loading7 } = useQuery({
    queryKey: ["sales-summary", 7],
    queryFn: () => apiClient.getSalesSummary(7),
  });

  const { data: summary30, isLoading: loading30 } = useQuery({
    queryKey: ["sales-summary", 30],
    queryFn: () => apiClient.getSalesSummary(30),
  });

  const currentSummary = windowDays === 7 ? summary7 : summary30;
  const isLoading = windowDays === 7 ? loading7 : loading30;

  // Prepare chart data (daily breakdown would need backend support)
  // For now, show summary stats
  const chartData = [
    { name: "Last 7 Days", revenue: summary7?.total_revenue || 0, quantity: summary7?.total_quantity || 0 },
    { name: "Last 30 Days", revenue: summary30?.total_revenue || 0, quantity: summary30?.total_quantity || 0 },
  ];

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Sales Summary</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setWindowDays(7)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                windowDays === 7
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setWindowDays(30)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                windowDays === 30
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              30 Days
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-medium text-blue-600">Total Revenue</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">
              ${currentSummary?.total_revenue.toFixed(2) || "0.00"}
            </p>
          </div>

          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-1">
              <ShoppingCart className="h-4 w-4 text-green-600" />
              <span className="text-xs font-medium text-green-600">Items Sold</span>
            </div>
            <p className="text-2xl font-bold text-green-900">
              {currentSummary?.total_quantity || 0}
            </p>
          </div>

          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-purple-600" />
              <span className="text-xs font-medium text-purple-600">Transactions</span>
            </div>
            <p className="text-2xl font-bold text-purple-900">
              {currentSummary?.transaction_count || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
            <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="revenue" fill="#8884d8" name="Revenue ($)" />
            <Bar yAxisId="right" dataKey="quantity" fill="#82ca9d" name="Quantity" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

