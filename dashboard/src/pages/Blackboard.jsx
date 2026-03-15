import React, { useState, useEffect } from 'react'
import { Card, Descriptions, Button, Tabs, Table, Tag, Space, message } from 'antd'
import { DatabaseOutlined, ReloadOutlined } from '@ant-design/icons'
import axios from 'axios'

const Blackboard = () => {
  const [blackboard, setBlackboard] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchBlackboard = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/blackboard')
      setBlackboard(response.data)
    } catch (error) {
      message.error('获取黑板状态失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBlackboard()
    const interval = setInterval(fetchBlackboard, 30000)
    return () => clearInterval(interval)
  }, [])

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      ellipsis: true
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colorMap = {
          'pending': 'default',
          'running': 'processing',
          'completed': 'success',
          'failed': 'error',
          'cancelled': 'warning'
        }
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>
      }
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => {
        const colorMap = {
          1: 'default',
          2: 'blue',
          3: 'orange',
          4: 'red'
        }
        const textMap = {
          1: '低',
          2: '中',
          3: '高',
          4: '紧急'
        }
        return <Tag color={colorMap[priority]}>{textMap[priority]}</Tag>
      }
    },
    {
      title: 'Agent角色',
      dataIndex: 'agent_role',
      key: 'agent_role',
      width: 120
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString()
    }
  ]

  const knowledgeColumns = [
    {
      title: '键',
      dataIndex: 'key',
      key: 'key',
      width: 200
    },
    {
      title: '值',
      dataIndex: 'value',
      key: 'value',
      ellipsis: true,
      render: (value) => {
        if (typeof value === 'object') {
          return <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(value, null, 2)}</pre>
        }
        return String(value)
      }
    },
    {
      title: 'Agent',
      dataIndex: 'agent',
      key: 'agent',
      width: 150
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString()
    }
  ]

  const resultColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      ellipsis: true
    },
    {
      title: 'Agent ID',
      dataIndex: 'agent_id',
      key: 'agent_id',
      width: 150
    },
    {
      title: '结果',
      dataIndex: 'value',
      key: 'value',
      ellipsis: true,
      render: (value) => {
        if (typeof value === 'object') {
          return <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(value, null, 2)}</pre>
        }
        return String(value)
      }
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString()
    }
  ]

  const agentColumns = [
    {
      title: 'Agent ID',
      dataIndex: 'id',
      key: 'id',
      width: 200
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 100
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type) => {
        const colorMap = {
          'main': 'purple',
          'sub': 'blue'
        }
        return <Tag color={colorMap[type]}>{type}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colorMap = {
          'idle': 'success',
          'busy': 'processing',
          'error': 'error'
        }
        const textMap = {
          'idle': '空闲',
          'busy': '忙碌',
          'error': '错误'
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      }
    }
  ]

  const dagColumns = [
    {
      title: 'DAG ID',
      dataIndex: 'id',
      key: 'id',
      width: 200
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '任务数',
      dataIndex: 'task_count',
      key: 'task_count',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString()
    }
  ]

  const tabItems = [
    {
      key: 'overview',
      label: '概览',
      children: blackboard && (
        <Descriptions column={2} bordered>
          <Descriptions.Item label="版本">{blackboard.version}</Descriptions.Item>
          <Descriptions.Item label="时间戳">{new Date(blackboard.timestamp).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="任务数">{blackboard.tasks.length}</Descriptions.Item>
          <Descriptions.Item label="知识数">{blackboard.knowledge.length}</Descriptions.Item>
          <Descriptions.Item label="结果数">{blackboard.results.length}</Descriptions.Item>
          <Descriptions.Item label="会话数">{blackboard.sessions.length}</Descriptions.Item>
          <Descriptions.Item label="Agent数">{blackboard.agents.length}</Descriptions.Item>
          <Descriptions.Item label="DAG数">{blackboard.dags.length}</Descriptions.Item>
        </Descriptions>
      )
    },
    {
      key: 'tasks',
      label: `任务 (${blackboard?.tasks.length || 0})`,
      children: (
        <Table
          columns={taskColumns}
          dataSource={blackboard?.tasks || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      )
    },
    {
      key: 'knowledge',
      label: `知识 (${blackboard?.knowledge.length || 0})`,
      children: (
        <Table
          columns={knowledgeColumns}
          dataSource={blackboard?.knowledge || []}
          rowKey="key"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      )
    },
    {
      key: 'results',
      label: `结果 (${blackboard?.results.length || 0})`,
      children: (
        <Table
          columns={resultColumns}
          dataSource={blackboard?.results || []}
          rowKey="task_id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      )
    },
    {
      key: 'agents',
      label: `Agent (${blackboard?.agents.length || 0})`,
      children: (
        <Table
          columns={agentColumns}
          dataSource={blackboard?.agents || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      )
    },
    {
      key: 'dags',
      label: `DAG (${blackboard?.dags.length || 0})`,
      children: (
        <Table
          columns={dagColumns}
          dataSource={blackboard?.dags || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      )
    }
  ]

  return (
    <div>
      <Card
        title="黑板状态"
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchBlackboard} loading={loading}>
            刷新
          </Button>
        }
      >
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

export default Blackboard