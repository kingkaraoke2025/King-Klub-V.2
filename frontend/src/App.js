import "@fontsource/cinzel/400.css";
import "@fontsource/cinzel/700.css";
import "@fontsource/cinzel/900.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "@fontsource/playfair-display/400.css";
import "@fontsource/playfair-display/500.css";
import "@fontsource/playfair-display/600-italic.css";

import "@/App.css";
import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import VotePopup from "@/components/VotePopup";
import useVoteNotification from "@/hooks/useVoteNotification";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import QueuePage from "@/pages/QueuePage";
import LeaderboardPage from "@/pages/LeaderboardPage";
import AccomplishmentsPage from "@/pages/AccomplishmentsPage";
import BattlesPage from "@/pages/BattlesPage";
import AdminPage from "@/pages/AdminPage";
import AdminLoginPage from "@/pages/AdminLoginPage";
import CheckInPage from "@/pages/CheckInPage";
import QRCheckInPage from "@/pages/QRCheckInPage";
import HowToEarnPage from "@/pages/HowToEarnPage";

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-royal-bg flex items-center justify-center">
        <div className="text-gold animate-pulse font-cinzel text-2xl">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (adminOnly && !user.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Main App Content with Vote Popup
const AppContent = () => {
  const { user, isAuthenticated } = useAuth();
  const [voteChallenge, setVoteChallenge] = useState(null);

  // Connect to WebSocket for vote notifications
  useVoteNotification(setVoteChallenge, () => setVoteChallenge(null));

  // Check for open voting on mount
  useEffect(() => {
    const checkOpenVoting = async () => {
      if (!isAuthenticated) return;
      try {
        const response = await axios.get(`${API}/challenges/voting-open`);
        if (response.data.voting_open && response.data.challenge) {
          setVoteChallenge(response.data.challenge);
        }
      } catch (error) {
        // Silently fail
      }
    };
    checkOpenVoting();
  }, [isAuthenticated]);

  const handleVote = (challengeId, performerId) => {
    // Vote already handled in VotePopup
    // Keep popup open until voting closes
  };

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/queue"
          element={
            <ProtectedRoute>
              <QueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/leaderboard"
          element={
            <ProtectedRoute>
              <LeaderboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/accomplishments"
          element={
            <ProtectedRoute>
              <AccomplishmentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/battles"
          element={
            <ProtectedRoute>
              <BattlesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute adminOnly>
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/qr-checkin"
          element={
            <ProtectedRoute adminOnly>
              <QRCheckInPage />
            </ProtectedRoute>
          }
        />
        <Route path="/checkin/:venueCode" element={<CheckInPage />} />
        <Route path="/how-to-earn" element={<HowToEarnPage />} />
      </Routes>
      
      {/* Global Vote Popup */}
      {isAuthenticated && voteChallenge && (
        <VotePopup
          challenge={voteChallenge}
          onVote={handleVote}
          onClose={() => setVoteChallenge(null)}
          userId={user?.id}
        />
      )}
      
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1A0B2E',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#FAFAF9',
          },
        }}
      />
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
