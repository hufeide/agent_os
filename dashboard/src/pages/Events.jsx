import React, { useState, useEffect } from 'react'
import { Card, List, Tag, Space, Button, Input, Select } from 'antd'
import { ThunderboltOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Search } = Input
const { Option } = Select

const Events = () => {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [filterType, setFilterType] = useState('all')
  const [searchText, setSearchText] = useState('')

  const fetchEvents = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/events?limit=100&grouped=true')
      const data = response.data
      
      if (data.grouped && data.events) {
        setEvents(data.events)
      } else {
        setEvents(data.events || [])
      }
    } catch (error) {
      console.error('Failed to fetch events:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
    const interval = setInterval(fetchEvents, 10000)
    return () => clearInterval(interval)
  }, [])

  const getEventColor = (type) => {
    switch (type) {
      case 'task_created':
        return 'blue'
      case 'task_started':
        return 'orange'
      case 'task_completed':
        return 'green'
      case 'task_failed':
        return 'red'
      case 'dag_updated':
        return 'purple'
      case 'new_task_generated':
        return 'cyan'
      case 'agent_registered':
        return 'geekblue'
      case 'agent_unregistered':
        return 'volcano'
      case 'skill_registered':
        return 'magenta'
      case 'skill_unregistered':
        return 'gold'
      case 'knowledge_updated':
        return 'lime'
      case 'result_updated':
        return 'default'
      default:
        return 'default'
    }
  }

  const getEventText = (type) => {
    switch (type) {
      case 'task_created':
        return '任务创建'
      case 'task_started':
        return '任务开始'
      case 'task_completed':
        return '任务完成'
      case 'task_failed':
        return '任务失败'
      case 'dag_updated':
        return 'DAG更新'
      case 'new_task_generated':
        return '新任务生成'
      case 'agent_registered':
        return 'Agent注册'
      case 'agent_unregistered':
        return 'Agent注销'
      case 'skill_registered':
        return '技能注册'
      case 'skill_unregistered':
        return '技能注销'
      case 'knowledge_updated':
        return '知识更新'
      case 'result_updated':
        return '结果更新'
      default:
        return type
    }
  }

  const filteredEvents = events.filter(event => {
    if (filterType !== 'all' && event.type !== filterType) {
      return false
    }
    if (searchText) {
      const searchLower = searchText.toLowerCase()
      return (
        event.type.toLowerCase().includes(searchLower) ||
        event.source.toLowerCase().includes(searchLower) ||
        JSON.stringify(event.data).toLowerCase().includes(searchLower)
      )
    }
    return true
  })

  const filteredSessions = events.filter(session => {
    if (searchText) {
      const searchLower = searchText.toLowerCase()
      return session.events.some(event =>
        event.type.toLowerCase().includes(searchLower) ||
        event.source.toLowerCase().includes(searchLower) ||
        JSON.stringify(event.data).toLowerCase().includes(searchLower)
      )
    }
    return true
  }).map(session => ({
    ...session,
    events: session.events.filter(event => {
      if (filterType !== 'all' && event.type !== filterType) {
        return false
      }
      if (searchText) {
        const searchLower = searchText.toLowerCase()
        return (
          event.type.toLowerCase().includes(searchLower) ||
          event.source.toLowerCase().includes(searchLower) ||
          JSON.stringify(event.data).toLowerCase().includes(searchLower)
        )
      }
      return true
    })
  })).filter(session => session.events.length > 0)

  const eventTypes = [...new Set(events.map(e => e.type))]

  const renderEventItem = (event) => (
    <List.Item>
      <List.Item.Meta
        avatar={<ThunderboltOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
        title={
          <Space>
            <Tag color={getEventColor(event.type)}>{getEventText(event.type)}</Tag>
            <span style={{ fontSize: 12, color: '#666' }}>
              {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Invalid Date'}
            </span>
          </Space>
        }
        description={
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <span style={{ fontWeight: 'bold' }}>来源: </span>
              <span>{event.source}</span>
            </div>
            <div>
              <span style={{ fontWeight: 'bold' }}>数据: </span>
              <pre style={{ 
                margin: 0, 
                padding: 8, 
                background: '#f5f5f5', 
                borderRadius: 4,
                fontSize: 12,
                maxHeight: 200,
                overflow: 'auto'
              }}>
                {JSON.stringify(event.data, null, 2)}
              </pre>
            </div>
          </Space>
        }
      />
    </List.Item>
  )

  const renderSessionItem = (session) => (
    <List.Item>
      <List.Item.Meta
        avatar={<ThunderboltOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
        title={
          <Space>
            <Tag color="blue">{session.session_name || session.session_id}</Tag>
            <span style={{ fontSize: 12, color: '#666' }}>
              {session.event_count} 个事件
            </span>
          </Space>
        }
        description={
          <div style={{ width: '100%' }}>
            <List
              size="small"
              dataSource={session.events}
              renderItem={renderEventItem}
              style={{ marginTop: 8 }}
            />
          </div>
        }
      />
    </List.Item>
  )

  return (
    <div>
      <Card
        title="事件日志"
        extra={
          <Space>
            <Select
              value={filterType}
              onChange={setFilterType}
              style={{ width: 150 }}
            >
              <Option value="all">全部类型</Option>
              {eventTypes.map(type => (
                <Option key={type} value={type}>{getEventText(type)}</Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={fetchEvents} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      >
        <Search
          placeholder="搜索事件..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16 }}
          allowClear
        />
        <List
          loading={loading}
          dataSource={events.length > 0 && events[0].session_id ? filteredSessions : filteredEvents}
          renderItem={events.length > 0 && events[0].session_id ? renderSessionItem : renderEventItem}
        />
      </Card>
    </div>
  )
}

export default Events