import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { LiffCheck } from './pages/LiffCheck';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/check" element={<LiffCheck />} />
        <Route path="/signup" element={<Navigate to="/check" replace />} />
        <Route path="/login" element={<Navigate to="/check" replace />} />
        <Route path="/profile" element={<Navigate to="/check" replace />} />
      </Routes>
    </Layout>
  );
}
