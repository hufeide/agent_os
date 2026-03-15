import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  RobotOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  SettingOutlined
} from '@ant-design/icons'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Tasks from './pages/Tasks'
import Events from './pages/Events'
import Blackboard from './pages/Blackboard'
import Skills from './pages/Skills'

const { Header, Content, Sider } = Layout

function App() {
  const [collapsed, setCollapsed] = useState(false)
  const [selectedKey, setSelectedKey] = useState('dashboard')
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer }
  } = theme.useToken()

  useEffect(() => {
    const path = location.pathname.replace('/', '')
    if (path) {
      setSelectedKey(path)
    }
  }, [location.pathname])

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘'
    },
    {
      key: 'agents',
      icon: <RobotOutlined />,
      label: 'Agent管理'
    },
    {
      key: 'tasks',
      icon: <NodeIndexOutlined />,
      label: '任务管理'
    },
    {
      key: 'events',
      icon: <ThunderboltOutlined />,
      label: '事件日志'
    },
    {
      key: 'blackboard',
      icon: <DatabaseOutlined />,
      label: '黑板状态'
    },
    {
      key: 'skills',
      icon: <SettingOutlined />,
      label: '技能管理'
    }
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: 18,
          fontWeight: 'bold'
        }}>
          {collapsed ? 'Agent OS' : 'Agent OS Dashboard'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => {
            setSelectedKey(key)
            navigate(`/${key}`)
          }}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: 0,
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingRight: 24
        }}>
          <div style={{ fontSize: 20, fontWeight: 'bold', marginLeft: 24 }}>
            主从分层Agent系统
          </div>
          <div style={{ color: '#666' }}>
            Version 2.0.0
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{
            padding: 24,
            minHeight: 360,
            background: colorBgContainer,
            borderRadius: 8
          }}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/events" element={<Events />} />
              <Route path="/blackboard" element={<Blackboard />} />
              <Route path="/skills" element={<Skills />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App