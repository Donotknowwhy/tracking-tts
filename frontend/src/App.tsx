import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ConfigProvider, Layout, theme } from 'antd'
import viVN from 'antd/locale/vi_VN'
import HomePage from './pages/HomePage'
import JobDetailPage from './pages/JobDetailPage'
import './App.css'

const { Content } = Layout

export default function App() {
  return (
    <ConfigProvider
      locale={viVN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1f4e78',
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <Content style={{ padding: '24px', maxWidth: 1040, margin: '0 auto', width: '100%' }}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/jobs/:jobId" element={<JobDetailPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Content>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  )
}
