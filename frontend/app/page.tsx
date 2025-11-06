import { InventoryTable } from "@/components/InventoryTable";
import { LowStockAlerts } from "@/components/LowStockAlerts";
import { SalesSummary } from "@/components/SalesSummary";
import { ReordersView } from "@/components/ReordersView";
import { VoiceLogsPanel } from "@/components/VoiceLogsPanel";
import { Header } from "@/components/Header";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Sales Summary - Full Width on Mobile, 2 cols on Large */}
          <div className="lg:col-span-2">
            <SalesSummary />
          </div>
          
          {/* Low Stock Alerts */}
          <div className="lg:col-span-1">
            <LowStockAlerts />
          </div>
        </div>

        {/* Reorders and Voice Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <ReordersView />
          <VoiceLogsPanel />
        </div>

        {/* Inventory Table - Full Width */}
        <div className="mt-6">
          <InventoryTable />
        </div>
      </div>
    </main>
  );
}

