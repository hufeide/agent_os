import React, { useState, useEffect } from 'react'
import { Card, List, Tag, Space, Button, Modal, Progress, Descriptions, message, Input, Form } from 'antd'
import { NodeIndexOutlined, ReloadOutlined, PlusOutlined } from '@ant-design/icons'
import axios from 'axios'

const Tasks = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [form] = Form.useForm()

  const fetchTasks = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/tasks')
      setTasks(response.data.tasks || [])
    } catch (error) {
      message.error('获取任务列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleCreateTask = async (values) => {
    try {
      await axios.post('/api/tasks', {
        description: values.description,
        context: values.context ? JSON.parse(values.context) : {}
      })
      message.success('任务创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchTasks()
    } catch (error) {
      message.error('任务创建失败')
      console.error(error)
    }
  }

  const handleViewDetails = async (task) => {
    try {
      const response = await axios.get(`/api/tasks/${task.dag_id}`)
      setSelectedTask({
        ...task,
        status: response.data
      })
      setDetailModalVisible(true)
    } catch (error) {
      message.error('获取任务详情失败')
      console.error(error)
    }
  }

  const getCompletionRate = (status) => {
    const total = status.total_tasks
    if (total === 0) return 0
    const completed = status.status_counts.completed || 0
    return Math.round((completed / total) * 100)
  }

  return (
    <div>
      <Card
        title="任务列表"
        extra={
          <Space>
            <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              创建任务
            </Button>
            <Button icon={<ReloadOutlined />} onClick={fetchTasks} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      >
        <List
          loading={loading}
          dataSource={tasks}
          renderItem={(task) => (
            <List.Item
              actions={[
                <Button type="link" onClick={() => handleViewDetails(task)}>
                  查看详情
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<NodeIndexOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={
                  <Space>
                    <span>{task.name}</span>
                    {task.is_completed && <Tag color="success">已完成</Tag>}
                    {!task.is_completed && task.total_tasks > 0 && <Tag color="processing">执行中</Tag>}
                    {!task.is_completed && task.total_tasks === 0 && <Tag color="blue">规划中</Tag>}
                  </Space>
                }
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>{task.description}</div>
                    <Space>
                      <span>子任务数: {task.total_tasks}</span>
                      <span>|</span>
                      <span>创建时间: {new Date(task.created_at).toLocaleString()}</span>
                    </Space>
                    {task.final_answer && (
                      <div style={{ marginTop: 8, padding: 8, backgroundColor: '#f0f2ff', borderRadius: 4 }}>
                        <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>最终回答:</div>
                        <div style={{ fontSize: 14, color: '#333' }}>
                          {task.final_answer.answer.length > 100 
                            ? task.final_answer.answer.substring(0, 100) + '...' 
                            : task.final_answer.answer}
                        </div>
                        {task.final_answer.method && (
                          <Tag color="blue" style={{ marginTop: 4 }}>
                            {task.final_answer.method}
                          </Tag>
                        )}
                      </div>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="创建新任务"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateTask}>
          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入任务描述" />
          </Form.Item>
          <Form.Item
            name="context"
            label="上下文 (JSON格式)"
            help="可选，提供额外的上下文信息"
          >
            <Input.TextArea rows={4} placeholder='{"key": "value"}' />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && (
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="DAG ID">{selectedTask.dag_id}</Descriptions.Item>
              <Descriptions.Item label="任务名称">{selectedTask.name}</Descriptions.Item>
              <Descriptions.Item label="描述">{selectedTask.description}</Descriptions.Item>
              <Descriptions.Item label="总任务数">{selectedTask.status.total_tasks}</Descriptions.Item>
              <Descriptions.Item label="完成进度">
                <Progress percent={getCompletionRate(selectedTask.status)} />
              </Descriptions.Item>
              <Descriptions.Item label="状态统计">
                <Space>
                  <Tag color="blue">待处理: {selectedTask.status.status_counts.pending || 0}</Tag>
                  <Tag color="orange">运行中: {selectedTask.status.status_counts.running || 0}</Tag>
                  <Tag color="green">已完成: {selectedTask.status.status_counts.completed || 0}</Tag>
                  <Tag color="red">失败: {selectedTask.status.status_counts.failed || 0}</Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedTask.created_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
            
            {selectedTask.final_answer && (
              <Card 
                title="最终回答" 
                style={{ marginTop: 16 }}
                extra={<Tag color="success">{selectedTask.final_answer.method}</Tag>}
              >
                <div style={{ marginBottom: 8 }}>
                  <strong>问题:</strong> {selectedTask.final_answer.question}
                </div>
                <div style={{ marginBottom: 8 }}>
                  <strong>回答:</strong>
                </div>
                <div style={{ 
                  padding: 12, 
                  backgroundColor: '#f6ffed', 
                  borderRadius: 4,
                  lineHeight: 1.6 
                }}>
                  {selectedTask.final_answer.answer}
                </div>
                {selectedTask.final_answer.summary && (
                  <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                    <strong>摘要:</strong> {selectedTask.final_answer.summary}
                  </div>
                )}
              </Card>
            )}
            
            {selectedTask.latest_result && !selectedTask.final_answer && (
              <Card title="最新结果" style={{ marginTop: 16 }}>
                <Descriptions column={1}>
                  <Descriptions.Item label="方法">{selectedTask.latest_result.method}</Descriptions.Item>
                  <Descriptions.Item label="类型">{selectedTask.latest_result.type}</Descriptions.Item>
                  {selectedTask.latest_result.original_question && (
                    <Descriptions.Item label="原始问题">
                      {selectedTask.latest_result.original_question}
                    </Descriptions.Item>
                  )}
                  {selectedTask.latest_result.answer_to_original_question && (
                    <Descriptions.Item label="最终回答">
                      <div style={{ 
                        padding: 12, 
                        backgroundColor: '#f6ffed', 
                        borderRadius: 4,
                        lineHeight: 1.6 
                      }}>
                        {selectedTask.latest_result.answer_to_original_question}
                      </div>
                    </Descriptions.Item>
                  )}
                  {selectedTask.latest_result.summary && (
                    <Descriptions.Item label="摘要">
                      {selectedTask.latest_result.summary}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            )}
            
            {selectedTask.completed_results && selectedTask.completed_results.length > 0 && (
              <Card title={`完成任务详情 (${selectedTask.completed_results.length}个)`} style={{ marginTop: 16 }}>
                {selectedTask.completed_results.map((result, index) => (
                  <div key={result.task_id} style={{ 
                    marginBottom: index < selectedTask.completed_results.length - 1 ? 16 : 0,
                    padding: 12,
                    border: '1px solid #e8e8e8',
                    borderRadius: 4
                  }}>
                    <div style={{ marginBottom: 8 }}>
                      <strong>任务:</strong> {result.task_name}
                    </div>
                    <Space>
                      <Tag color="blue">{result.result.method}</Tag>
                      {result.result.type && <Tag color="purple">{result.result.type}</Tag>}
                    </Space>
                    {result.final_answer && (
                      <div style={{ marginTop: 8 }}>
                        <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>最终回答:</div>
                        <div style={{ 
                          padding: 8, 
                          backgroundColor: '#f0f2ff', 
                          borderRadius: 4,
                          fontSize: 13 
                        }}>
                          {result.final_answer}
                        </div>
                      </div>
                    )}
                    {result.result.findings && (
                      <div style={{ marginTop: 8 }}>
                        <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>研究发现:</div>
                        <div style={{ fontSize: 13 }}>
                          {Array.isArray(result.result.findings) 
                            ? result.result.findings.map((f, i) => (
                                <div key={i} style={{ marginBottom: 4 }}>
                                  • {typeof f === 'string' ? f : JSON.stringify(f)}
                                </div>
                              ))
                            : result.result.findings}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </Card>
            )}
            
            {selectedTask.combined_final_answer && (
              <Card 
                title="综合最终回答" 
                style={{ marginTop: 16 }}
                extra={<Tag color="green">整合{selectedTask.combined_final_answer.task_count}个任务</Tag>}
              >
                <div style={{ marginBottom: 8 }}>
                  <strong>问题:</strong> {selectedTask.combined_final_answer.question}
                </div>
                <div style={{ marginBottom: 8 }}>
                  <strong>综合回答:</strong>
                </div>
                <div style={{ 
                  padding: 12, 
                  backgroundColor: '#fff7e6', 
                  borderRadius: 4,
                  lineHeight: 1.6,
                  fontSize: 14
                }}>
                  {selectedTask.combined_final_answer.answer}
                </div>
                {selectedTask.combined_final_answer.summary && (
                  <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                    <strong>摘要:</strong> {selectedTask.combined_final_answer.summary}
                  </div>
                )}
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Tasks