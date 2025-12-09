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
import TripDetailPage from './pages/travel/TripDetailPage';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/auth/login" element={<LoginPage />} />
          <Route path="/auth/register" element={<RegisterPage />} />
          <Route path="/" element={<Navigate to="/social" replace />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              {/* Social */}
              <Route path="/social" element={<FeedPage />} />
              <Route path="/social/create" element={<CreatePostPage />} />
              <Route path="/social/post/:id" element={<PostDetailPage />} />
              
              {/* Chat */}
              <Route path="/chat" element={<ChatPage />} />

              {/* Travel */}
              <Route path="/travel" element={<MyTripsPage />} />
              <Route path="/travel/public" element={<PublicTripsPage />} />
              <Route path="/travel/trips/:id" element={<TripDetailPage />} />

              {/* Profile */}
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/profile/edit" element={<ManageProfilePage />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
