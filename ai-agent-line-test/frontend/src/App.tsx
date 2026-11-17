import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LiffCheck } from './pages/LiffCheck';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LiffCheck />} />
        <Route path="/check" element={<LiffCheck />} />
        <Route path="/signup" element={<Navigate to="/" replace />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/profile" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
