import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Timeline, List, Tag, Space, Button } from 'antd'
import { 
  RobotOutlined, 
  NodeIndexOutlined, 
  ThunderboltOutlined, 
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'
import axios from 'axios'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    totalTasks: 0,
    runningTasks: 0,
    completedTasks: 0,
    failedTasks: 0
  })
  const [recentEvents, setRecentEvents] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchStats = async () => {
    try {
      setLoading(true)
      const [agentsRes, tasksRes, eventsRes] = await Promise.all([
        axios.get('/api/agents'),
        axios.get('/api/tasks'),
        axios.get('/api/events?limit=10')
      ])

      const agents = agentsRes.data
      const tasks = tasksRes.data
      const events = eventsRes.data

      let runningTasks = 0
      let completedTasks = 0
      let failedTasks = 0

      tasks.tasks.forEach(task => {
        if (task.is_completed) {
          completedTasks++
        } else {
          runningTasks++
        }
      })

      setStats({
        totalAgents: agents.sub_agents.length + 1,
        activeAgents: agents.sub_agents.filter(a => a.status === 'idle').length,
        totalTasks: tasks.total,
        runningTasks,
        completedTasks,
        failedTasks
      })

      setRecentEvents(events.events || [])
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const getEventIcon = (type) => {
    switch (type) {
      case 'task_created':
        return <NodeIndexOutlined style={{ color: '#1890ff' }} />
      case 'task_started':
        return <SyncOutlined spin style={{ color: '#faad14' }} />
      case 'task_completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'task_failed':
        return <ThunderboltOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
    }
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总Agent数"
              value={stats.totalAgents}
              prefix={<RobotOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="活跃Agent"
              value={stats.activeAgents}
              prefix={<CheckCircleOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="总任务数"
              value={stats.totalTasks}
              prefix={<NodeIndexOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="已完成任务"
              value={stats.completedTasks}
              prefix={<CheckCircleOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="任务状态" loading={loading}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <div style={{ marginBottom: 8 }}>
                  <span>运行中</span>
                  <span style={{ float: 'right' }}>{stats.runningTasks}</span>
                </div>
                <Progress percent={stats.totalTasks > 0 ? (stats.runningTasks / stats.totalTasks) * 100 : 0} status="active" strokeColor="#faad14" />
              </div>
              <div>
                <div style={{ marginBottom: 8 }}>
                  <span>已完成</span>
                  <span style={{ float: 'right' }}>{stats.completedTasks}</span>
                </div>
                <Progress percent={stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0} status="success" strokeColor="#52c41a" />
              </div>
              <div>
                <div style={{ marginBottom: 8 }}>
                  <span>失败</span>
                  <span style={{ float: 'right' }}>{stats.failedTasks}</span>
                </div>
                <Progress percent={stats.totalTasks > 0 ? (stats.failedTasks / stats.totalTasks) * 100 : 0} status="exception" strokeColor="#ff4d4f" />
              </div>
            </Space>
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title="最近事件" 
            loading={loading}
            extra={<Button onClick={fetchStats} size="small">刷新</Button>}
          >
            <Timeline
              items={recentEvents.map(event => ({
                children: (
                  <div>
                    <div style={{ marginBottom: 4 }}>
                      <Tag color="blue">{event.type}</Tag>
                      <span style={{ marginLeft: 8, fontSize: 12, color: '#666' }}>
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div style={{ fontSize: 12 }}>
                      {event.source}
                    </div>
                  </div>
                ),
                dot: getEventIcon(event.type)
              }))}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard