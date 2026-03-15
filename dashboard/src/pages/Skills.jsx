import React, { useState, useEffect } from 'react'
import { Card, List, Tag, Space, Button, Modal, Form, Input, Select, message, Descriptions } from 'antd'
import { SettingOutlined, ReloadOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { TextArea } = Input

const Skills = () => {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedSkill, setSelectedSkill] = useState(null)
  const [form] = Form.useForm()

  const fetchSkills = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/skills')
      setSkills(response.data.skills || [])
    } catch (error) {
      message.error('获取技能列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSkills()
    const interval = setInterval(fetchSkills, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleCreateSkill = async (values) => {
    try {
      await axios.post('/api/skills', {
        name: values.name,
        description: values.description,
        type: values.type,
        capabilities: values.capabilities ? values.capabilities.split(',').map(c => c.trim()) : [],
        config: values.config ? JSON.parse(values.config) : {}
      })
      message.success('技能注册成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchSkills()
    } catch (error) {
      message.error('技能注册失败')
      console.error(error)
    }
  }

  const handleDeleteSkill = async (skillId) => {
    try {
      await axios.delete(`/api/skills/${skillId}`)
      message.success('技能注销成功')
      fetchSkills()
    } catch (error) {
      message.error('技能注销失败')
      console.error(error)
    }
  }

  const handleViewDetails = (skill) => {
    setSelectedSkill(skill)
    setDetailModalVisible(true)
  }

  const getSkillTypeColor = (type) => {
    switch (type) {
      case 'llm':
        return 'purple'
      case 'function':
        return 'blue'
      case 'api':
        return 'green'
      case 'tool':
        return 'orange'
      default:
        return 'default'
    }
  }

  const getSkillTypeText = (type) => {
    switch (type) {
      case 'llm':
        return 'LLM'
      case 'function':
        return '函数'
      case 'api':
        return 'API'
      case 'tool':
        return '工具'
      default:
        return type
    }
  }

  return (
    <div>
      <Card
        title="技能管理"
        extra={
          <Space>
            <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              注册技能
            </Button>
            <Button icon={<ReloadOutlined />} onClick={fetchSkills} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      >
        <List
          loading={loading}
          dataSource={skills}
          renderItem={(skill) => (
            <List.Item
              actions={[
                <Button type="link" onClick={() => handleViewDetails(skill)}>
                  查看详情
                </Button>,
                <Button 
                  type="link" 
                  danger 
                  icon={<DeleteOutlined />}
                  onClick={() => handleDeleteSkill(skill.id)}
                >
                  注销
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<SettingOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={
                  <Space>
                    <span>{skill.name}</span>
                    <Tag color={getSkillTypeColor(skill.type)}>
                      {getSkillTypeText(skill.type)}
                    </Tag>
                    {skill.is_active ? <Tag color="success">活跃</Tag> : <Tag color="default">停用</Tag>}
                  </Space>
                }
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>{skill.description}</div>
                    <Space>
                      <span>能力: </span>
                      {skill.required_capabilities.map(cap => (
                        <Tag key={cap} color="blue">{cap}</Tag>
                      ))}
                    </Space>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="注册新技能"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateSkill}>
          <Form.Item
            name="name"
            label="技能名称"
            rules={[{ required: true, message: '请输入技能名称' }]}
          >
            <Input placeholder="请输入技能名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <TextArea rows={3} placeholder="请输入技能描述" />
          </Form.Item>
          <Form.Item
            name="type"
            label="技能类型"
            rules={[{ required: true, message: '请选择技能类型' }]}
          >
            <Select placeholder="请选择技能类型">
              <Option value="llm">LLM</Option>
              <Option value="function">函数</Option>
              <Option value="api">API</Option>
              <Option value="tool">工具</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="capabilities"
            label="能力列表"
            help="用逗号分隔多个能力"
          >
            <Input placeholder="例如: research, analysis, writing" />
          </Form.Item>
          <Form.Item
            name="config"
            label="配置 (JSON格式)"
            help="可选，提供技能配置"
          >
            <TextArea rows={4} placeholder='{"key": "value"}' />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="技能详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {selectedSkill && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="技能ID">{selectedSkill.id}</Descriptions.Item>
            <Descriptions.Item label="名称">{selectedSkill.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{selectedSkill.description}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={getSkillTypeColor(selectedSkill.type)}>
                {getSkillTypeText(selectedSkill.type)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedSkill.is_active ? 'success' : 'default'}>
                {selectedSkill.is_active ? '活跃' : '停用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="能力">
              {selectedSkill.required_capabilities.map(cap => (
                <Tag key={cap} color="blue">{cap}</Tag>
              ))}
            </Descriptions.Item>
            <Descriptions.Item label="配置">
              <pre style={{ margin: 0, fontSize: 12 }}>
                {JSON.stringify(selectedSkill.config || {}, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default Skills