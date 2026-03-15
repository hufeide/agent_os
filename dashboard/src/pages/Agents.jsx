import React, { useState, useEffect } from 'react'
import { Card, List, Tag, Space, Button, Descriptions, Modal, message } from 'antd'
import { RobotOutlined, ReloadOutlined } from '@ant-design/icons'
import axios from 'axios'

const Agents = () => {
  const [agents, setAgents] = useState([])
  const [mainAgent, setMainAgent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [modalVisible, setModalVisible] = useState(false)

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/agents')
      setMainAgent(response.data.main_agent)
      setAgents(response.data.sub_agents)
    } catch (error) {
      message.error('获取Agent列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
    const interval = setInterval(fetchAgents, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleViewDetails = (agent) => {
    setSelectedAgent(agent)
    setModalVisible(true)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'idle':
        return 'success'
      case 'busy':
        return 'processing'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'idle':
        return '空闲'
      case 'busy':
        return '忙碌'
      case 'error':
        return '错误'
      default:
        return status
    }
  }

  return (
    <div>
      <Card
        title="主Agent (Planner)"
        extra={<Button icon={<ReloadOutlined />} onClick={fetchAgents} loading={loading}>刷新</Button>}
        style={{ marginBottom: 16 }}
      >
        {mainAgent ? (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="Agent ID">{mainAgent.agent_id}</Descriptions.Item>
            <Descriptions.Item label="名称">{mainAgent.agent_name}</Descriptions.Item>
            <Descriptions.Item label="活跃DAG数">{mainAgent.active_dags}</Descriptions.Item>
            <Descriptions.Item label="DAG列表">
              {mainAgent.dag_ids.length > 0 ? mainAgent.dag_ids.join(', ') : '无'}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <div>加载中...</div>
        )}
      </Card>

      <Card
        title="子Agent Workers"
        extra={<Button icon={<ReloadOutlined />} onClick={fetchAgents} loading={loading}>刷新</Button>}
      >
        <List
          loading={loading}
          dataSource={agents}
          renderItem={(agent) => (
            <List.Item
              actions={[
                <Button type="link" onClick={() => handleViewDetails(agent)}>
                  查看详情
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<RobotOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={
                  <Space>
                    <span>{agent.name}</span>
                    <Tag color={getStatusColor(agent.status)}>{getStatusText(agent.status)}</Tag>
                  </Space>
                }
                description={
                  <Space>
                    <span>ID: {agent.agent_id}</span>
                    <span>|</span>
                    <span>角色: {agent.role}</span>
                    <span>|</span>
                    <span>当前任务: {agent.current_task_id || '无'}</span>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="Agent详情"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedAgent && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="Agent ID">{selectedAgent.agent_id}</Descriptions.Item>
            <Descriptions.Item label="名称">{selectedAgent.name}</Descriptions.Item>
            <Descriptions.Item label="角色">{selectedAgent.role}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedAgent.status)}>
                {getStatusText(selectedAgent.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前任务ID">{selectedAgent.current_task_id || '无'}</Descriptions.Item>
            <Descriptions.Item label="能力">
              {selectedAgent.capabilities.map(cap => (
                <Tag key={cap} color="blue">{cap}</Tag>
              ))}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default Agents