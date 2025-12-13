import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages - Auth
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ProfilePage from './pages/auth/ProfilePage';
import ManageProfilePage from './pages/auth/ManageProfilePage';

// Pages - Social
import FeedPage from './pages/social/FeedPage';
import CreatePostPage from './pages/social/CreatePostPage';
import PostDetailPage from './pages/social/PostDetailPage';
import ChatPage from './pages/social/ChatPage';

// Pages - Travel
import MyTripsPage from './pages/travel/MyTripsPage';
import PublicTripsPage from './pages/travel/PublicTripsPage';
import TravelPage from './pages/travel/TravelPage';
import TripDetailPage from './pages/travel/TripDetailPage';

// Admin
import AdminLayout from './admin/components/AdminLayout';
import AdminResourcePage from './admin/pages/AdminResourcePage';
import AiChatPage from './pages/ai/AiChatPage';

import { Toaster } from 'react-hot-toast';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Toaster position="top-right" />
        <Routes>
          {/* Public Routes */}
          <Route path="/auth/login" element={<LoginPage />} />
          <Route path="/auth/register" element={<RegisterPage />} />
          <Route path="/" element={<Navigate to="/social" replace />} />

          {/* Admin Routes */}
          <Route path="/admin" element={<AdminLayout />}>
             <Route index element={<Navigate to="users" replace />} />
             <Route path=":resourceName" element={<AdminResourcePage />} />
          </Route>

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              {/* Social */}
              <Route path="/social" element={<FeedPage />} />
              <Route path="/social/create" element={<CreatePostPage />} />
              <Route path="/social/post/:id" element={<PostDetailPage />} />
              
              {/* Chat */}
              <Route path="/chat" element={<ChatPage />} />

              {/* AI */}
              <Route path="/ai-assistant" element={<AiChatPage />} />

              {/* Travel */}
              <Route path="/travel" element={<TravelPage />} />
              <Route path="/travel/my-trips" element={<MyTripsPage />} />
              <Route path="/travel/public" element={<PublicTripsPage />} />
              <Route path="/travel/:tripId" element={<TripDetailPage />} />
              
              {/* Profile */}
              <Route path="/profile/:userId" element={<ProfilePage />} />
              <Route path="/profile/edit" element={<ManageProfilePage />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/social" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
