import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Tag, Button, Modal, Timeline, Spin, Alert, Tabs, Select, Space, Typography, Divider, Statistic } from 'antd'
import { 
  RobotOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  SyncOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
  ApiOutlined,
  FileTextOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title, Text, Paragraph } = Typography

const AgentInteraction = () => {
  const [dagList, setDagList] = useState([])
  const [selectedDagId, setSelectedDagId] = useState(null)
  const [interactionGraph, setInteractionGraph] = useState(null)
  const [agentDetails, setAgentDetails] = useState(null)
  const [taskDetails, setTaskDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [detailsModalVisible, setDetailsModalVisible] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchDagList = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/tasks')
      console.log('DAG list response:', response.data)
      if (response.data && response.data.tasks) {
        setDagList(response.data.tasks)
        console.log('DAG list set:', response.data.tasks)
        if (!selectedDagId && response.data.tasks.length > 0) {
          setSelectedDagId(response.data.tasks[0].dag_id)
          console.log('Selected DAG ID:', response.data.tasks[0].dag_id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch DAG list:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchInteractionGraph = async (dagId) => {
    try {
      setLoading(true)
      console.log('Fetching interaction graph for DAG:', dagId)
      const response = await axios.get(`/api/agent-interaction-graph/${dagId}`)
      console.log('Interaction graph response:', response.data)
      setInteractionGraph(response.data)
      console.log('Interaction graph state set')
    } catch (error) {
      console.error('Failed to fetch interaction graph:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAgentDetails = async (agentId) => {
    try {
      const response = await axios.get(`/api/agent-details/${agentId}`)
      console.log('Agent details response:', response.data)
      setAgentDetails(response.data)
    } catch (error) {
      console.error('Failed to fetch agent details:', error)
      setAgentDetails({
        agent_id: agentId,
        name: 'Error',
        role: 'unknown',
        status: 'error',
        error: error.message || 'Failed to fetch agent details'
      })
    }
  }

  const fetchTaskDetails = async (taskId) => {
    try {
      const response = await axios.get(`/api/task-details/${taskId}`)
      setTaskDetails(response.data)
    } catch (error) {
      console.error('Failed to fetch task details:', error)
    }
  }

  const handleNodeClick = async (node) => {
    setSelectedNode(node)
    setDetailsModalVisible(true)

    if (node.type === 'sub' || node.type === 'main') {
      await fetchAgentDetails(node.id)
    } else if (node.type === 'task') {
      await fetchTaskDetails(node.id)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'idle':
        return 'success'
      case 'running':
      case 'busy':
        return 'processing'
      case 'failed':
      case 'error':
        return 'error'
      case 'pending':
      case 'unknown':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined />
      case 'running':
        return <SyncOutlined spin />
      case 'failed':
        return <CloseCircleOutlined />
      case 'pending':
        return <ClockCircleOutlined />
      default:
        return <ClockCircleOutlined />
    }
  }

  const renderNode = (node) => {
    const statusColor = getStatusColor(node.status)
    const statusIcon = getStatusIcon(node.status)

    return (
      <Card
        key={node.id}
        size="small"
        style={{
          margin: '8px',
          cursor: 'pointer',
          border: selectedNode?.id === node.id ? '2px solid #1890ff' : '1px solid #d9d9d9',
          backgroundColor: node.type === 'main' ? '#e6f7ff' : node.type === 'sub' ? '#f6ffed' : '#fff7e6'
        }}
        onClick={() => handleNodeClick(node)}
        hoverable
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {node.type === 'main' && <RobotOutlined style={{ fontSize: '20px', color: '#1890ff' }} />}
          {node.type === 'sub' && <RobotOutlined style={{ fontSize: '16px', color: '#52c41a' }} />}
          {node.type === 'task' && <FileTextOutlined style={{ fontSize: '16px', color: '#faad14' }} />}
          
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 'bold', fontSize: '12px' }}>
              {node.name}
            </div>
            {node.role && (
              <Tag color="blue" style={{ fontSize: '10px', marginTop: '4px' }}>
                {node.role}
              </Tag>
            )}
            <div style={{ marginTop: '4px' }}>
              <Tag color={statusColor} icon={statusIcon} style={{ fontSize: '10px' }}>
                {node.status}
              </Tag>
            </div>
          </div>
        </div>
      </Card>
    )
  }

  const renderGraph = () => {
    console.log('renderGraph called, interactionGraph:', interactionGraph)
    if (!interactionGraph) {
      return <div style={{ textAlign: 'center', padding: '40px' }}>暂无交互图数据</div>
    }

    const { nodes, edges, statistics } = interactionGraph
    console.log('Rendering graph with:', { nodes: nodes.length, edges: edges.length, statistics })
    
    if (!nodes || !Array.isArray(nodes)) {
      return <div style={{ textAlign: 'center', padding: '40px' }}>节点数据格式错误</div>
    }
    
    if (!edges || !Array.isArray(edges)) {
      return <div style={{ textAlign: 'center', padding: '40px' }}>边数据格式错误</div>
    }

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={6}>
            <Statistic title="总Agent数" value={statistics.total_agents} prefix={<RobotOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="总任务数" value={statistics.total_tasks} prefix={<FileTextOutlined />} />
          </Col>
          <Col span={4}>
            <Statistic 
              title="已完成" 
              value={statistics.completed_tasks} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />} 
            />
          </Col>
          <Col span={4}>
            <Statistic 
              title="进行中" 
              value={statistics.pending_tasks} 
              valueStyle={{ color: '#faad14' }}
              prefix={<SyncOutlined spin />} 
            />
          </Col>
          <Col span={4}>
            <Statistic 
              title="失败" 
              value={statistics.failed_tasks} 
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />} 
            />
          </Col>
        </Row>

        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
          {nodes.map(node => renderNode(node))}
        </div>

        <Divider />

        <Title level={4}>依赖关系</Title>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {edges.map((edge, index) => (
            <div key={index} style={{ padding: '8px', borderBottom: '1px solid #f0f0f0' }}>
              <Space>
                <Tag color="blue">{edge.from}</Tag>
                <span style={{ color: '#999' }}>-</span>
                <Tag color={edge.type === 'dependency' ? 'orange' : 'green'}>{edge.label}</Tag>
                <span style={{ color: '#999' }}>-</span>
                <Tag color="blue">{edge.to}</Tag>
              </Space>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderAgentDetails = () => {
    if (!agentDetails) return null;

    console.log('Rendering agent details:', agentDetails)

    try {
      return (
      <div>
        <Title level={4}>Agent详细信息</Title>
        <Row gutter={16}>
          <Col span={12}>
            <Card title="基本信息" size="small">
              <p><strong>Agent ID:</strong> {agentDetails.agent_id || 'N/A'}</p>
              <p><strong>角色:</strong> {agentDetails.role || 'N/A'}</p>
              <p><strong>状态:</strong> <Tag color={getStatusColor(agentDetails.status)}>{agentDetails.status || 'unknown'}</Tag></p>
              <p><strong>当前任务:</strong> {agentDetails.current_task?.name || '无'}</p>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="统计信息" size="small">
              <Statistic 
                title="已执行任务" 
                value={agentDetails.statistics?.total_tasks_executed || 0} 
                prefix={<CheckCircleOutlined />} 
              />
              <Statistic 
                title="成功率" 
                value={agentDetails.statistics?.successful_tasks || 0} 
                suffix={`/ ${agentDetails.statistics?.total_tasks_executed || 0}`}
                valueStyle={{ color: '#52c41a' }}
              />
              <Statistic 
                title="总工具调用" 
                value={agentDetails.statistics?.total_tool_calls || 0} 
                prefix={<ApiOutlined />} 
              />
            </Card>
          </Col>
        </Row>

        <Card title="工作记忆" size="small" style={{ marginTop: '16px' }}>
          {agentDetails.working_memory && Array.isArray(agentDetails.working_memory) && agentDetails.working_memory.length > 0 ? (
            <div style={{ maxHeight: '300px', overflowY: 'auto', paddingRight: '10px' }}>
              <Timeline>
                {agentDetails.working_memory.map((item, index) => (
                  <Timeline.Item key={index}>
                    <div style={{ wordBreak: 'break-word' }}>
                      {typeof item === 'string' 
                        ? item 
                        : typeof item === 'object' 
                          ? JSON.stringify(item, null, 2)
                          : String(item)}
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          ) : (
            <Alert message="暂无工作记忆" type="info" />
          )}
        </Card>

        <Card title="工具调用历史" size="small" style={{ marginTop: '16px' }}>
          {agentDetails.tool_calls && Array.isArray(agentDetails.tool_calls) && agentDetails.tool_calls.length > 0 ? (
            <Timeline>
              {agentDetails.tool_calls.map((call, index) => (
                <Timeline.Item key={index}>
                  <Space direction="vertical">
                    <Text strong>{call.tool_name || 'Unknown Tool'}</Text>
                    <Text type="secondary">{call.timestamp || 'No timestamp'}</Text>
                    <Tag color={call.success ? 'success' : 'error'}>
                      {call.success ? '成功' : '失败'}
                    </Tag>
                    {call.result && typeof call.result === 'object' && (
                      <Paragraph ellipsis={{ rows: 2 }} style={{ fontSize: '12px' }}>
                        {typeof call.result === 'string' 
                          ? call.result 
                          : JSON.stringify(call.result).substring(0, 200) + '...'}
                      </Paragraph>
                    )}
                  </Space>
                </Timeline.Item>
              ))}
            </Timeline>
          ) : (
            <Alert message="暂无工具调用记录" type="info" />
          )}
        </Card>
      </div>
      )
    } catch (error) {
      console.error('Error rendering agent details:', error)
      return (
        <Alert 
          message="渲染Agent详细信息时出错" 
          description={error.message || '未知错误'} 
          type="error" 
        />
      )
    }
  }

  const renderTaskDetails = () => {
    if (!taskDetails) return null

    return (
      <div>
        <Title level={4}>任务详细信息</Title>
        <Card title="基本信息" size="small">
          <p><strong>任务ID:</strong> {taskDetails.task_id}</p>
          <p><strong>任务名称:</strong> {taskDetails.task_name}</p>
          <p><strong>描述:</strong> {taskDetails.description}</p>
          <p><strong>状态:</strong> <Tag color={getStatusColor(taskDetails.status)}>{taskDetails.status}</Tag></p>
          <p><strong>优先级:</strong> {taskDetails.priority}</p>
          <p><strong>Agent角色:</strong> {taskDetails.agent_role}</p>
        </Card>

        <Card title="执行结果" size="small" style={{ marginTop: '16px' }}>
          {taskDetails.result ? (
            <pre style={{ maxHeight: '400px', overflowY: 'auto', fontSize: '12px' }}>
              {JSON.stringify(taskDetails.result, null, 2)}
            </pre>
          ) : (
            <Alert message="暂无执行结果" type="info" />
          )}
        </Card>

        {taskDetails.error && (
          <Card title="错误信息" size="small" style={{ marginTop: '16px' }}>
            <Alert message={taskDetails.error} type="error" />
          </Card>
        )}
      </div>
    )
  }

  useEffect(() => {
    fetchDagList()
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (selectedDagId) {
          fetchInteractionGraph(selectedDagId)
        }
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [selectedDagId, autoRefresh])

  useEffect(() => {
    if (selectedDagId) {
      fetchInteractionGraph(selectedDagId)
    }
  }, [selectedDagId])

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>Agent交互图</Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={() => {
              fetchDagList()
              if (selectedDagId) {
                fetchInteractionGraph(selectedDagId)
              }
            }}
          >
            刷新
          </Button>
          <Button 
            type={autoRefresh ? 'primary' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '自动刷新: 开' : '自动刷新: 关'}
          </Button>
        </Space>
      </div>

      <Card>
        <div style={{ marginBottom: '16px' }}>
          <Text strong>选择DAG:</Text>
          <Select
            style={{ width: '100%', marginTop: '8px' }}
            value={selectedDagId}
            onChange={setSelectedDagId}
            loading={loading}
            options={dagList.map(dag => ({
              label: `${dag.name} (${dag.dag_id.substring(0, 8)}...)`,
              value: dag.dag_id
            }))}
          />
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
          </div>
        ) : (
          renderGraph()
        )}
      </Card>

      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>节点详情</span>
          </Space>
        }
        open={detailsModalVisible}
        onCancel={() => {
          setDetailsModalVisible(false)
          setAgentDetails(null)
          setTaskDetails(null)
        }}
        width={800}
        footer={null}
      >
        {selectedNode && (
          <div>
            <Alert 
              message={
                <Space>
                  <span>节点类型: {selectedNode.type}</span>
                  <span>名称: {selectedNode.name}</span>
                </Space>
              }
              type="info"
              style={{ marginBottom: '16px' }}
            />
            
            <Tabs
              items={[
                {
                  key: 'details',
                  label: '详细信息',
                  children: (
                    <div>
                      {agentDetails && renderAgentDetails()}
                      {taskDetails && renderTaskDetails()}
                    </div>
                  )
                }
              ]}
            />
          </div>
        )}
      </Modal>
    </div>
  )
}

export default AgentInteraction