import { Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import Alerts from "./pages/Alerts";
import Analyze from "./pages/Analyze";
import Dashboard from "./pages/Dashboard";
import EquipmentDetail from "./pages/EquipmentDetail";
import Landing from "./pages/Landing";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main className="content-shell">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/equipment/:id" element={<EquipmentDetail />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/predictions" element={<Navigate to="/analyze" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
