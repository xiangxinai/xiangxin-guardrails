import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Switch, message, Space, Popconfirm, Descriptions, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ApiOutlined } from '@ant-design/icons';
import axios from 'axios';

interface ProxyModel {
  id: string;
  config_name: string;
  model_name: string;
  enabled: boolean;
  block_on_input_risk: boolean;
  block_on_output_risk: boolean;
  enable_reasoning_detection: boolean;
  stream_chunk_size: number;
  created_at: string;
}

interface ProxyModelFormData {
  config_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  enabled?: boolean;
  block_on_input_risk?: boolean;
  block_on_output_risk?: boolean;
  enable_reasoning_detection?: boolean;
  stream_chunk_size?: number;
}

const ProxyModelManagement: React.FC = () => {
  const [models, setModels] = useState<ProxyModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<ProxyModel | null>(null);
  const [viewingModel, setViewingModel] = useState<ProxyModel | null>(null);
  const [advancedVisible, setAdvancedVisible] = useState(false);
  const [formKey, setFormKey] = useState(0); // 用于强制重新渲染表单
  const [form] = Form.useForm();
  
  // 直接管理开关状态（极简配置）
  const [switchStates, setSwitchStates] = useState({
    enabled: true,
    block_on_input_risk: false,  // 默认不阻断
    block_on_output_risk: false, // 默认不阻断
    enable_reasoning_detection: true, // 默认开启
    stream_chunk_size: 50, // 默认每50个chunk检测一次
  });


  // 获取模型列表
  const fetchModels = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get('/api/v1/proxy/models', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setModels(response.data.data);
      } else {
        message.error('获取模型配置失败');
      }
    } catch (error) {
      console.error('获取模型配置失败:', error);
      message.error('获取模型配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  // 获取模型详细信息（用于编辑）
  const fetchModelDetail = async (modelId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`/api/v1/proxy/models/${modelId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        return response.data.data;
      } else {
        message.error('获取模型详情失败');
        return null;
      }
    } catch (error) {
      console.error('获取模型详情失败:', error);
      message.error('获取模型详情失败');
      return null;
    }
  };

  // 显示创建/编辑弹窗
  const showModal = async (model?: ProxyModel) => {
    setEditingModel(model || null);
    
    if (model) {
      // 编辑模式：先获取完整数据，再显示弹窗
      const modelDetail = await fetchModelDetail(model.id);
      if (modelDetail) {
        console.log('=== 编辑模式 - 从服务器获取的数据 ===');
        console.log('enabled:', modelDetail.enabled, typeof modelDetail.enabled);
        console.log('block_on_input_risk:', modelDetail.block_on_input_risk, typeof modelDetail.block_on_input_risk);
        console.log('block_on_output_risk:', modelDetail.block_on_output_risk, typeof modelDetail.block_on_output_risk);
        console.log('enable_reasoning_detection:', modelDetail.enable_reasoning_detection, typeof modelDetail.enable_reasoning_detection);
        
        // 同步设置表单值和开关状态
        const formValues = {
          config_name: modelDetail.config_name,
          api_base_url: modelDetail.api_base_url,
          model_name: modelDetail.model_name,
        };
        
        const switchValues = {
          enabled: modelDetail.enabled,
          block_on_input_risk: modelDetail.block_on_input_risk,
          block_on_output_risk: modelDetail.block_on_output_risk,
          enable_reasoning_detection: modelDetail.enable_reasoning_detection !== false,
          stream_chunk_size: modelDetail.stream_chunk_size || 50,
        };
        
        // 重置表单并设置值
        form.resetFields();
        form.setFieldsValue(formValues);
        setSwitchStates(switchValues);
        
        // 更新表单key并显示弹窗
        setFormKey(prev => prev + 1);
        setIsModalVisible(true);
      } else {
        message.error('获取模型详情失败，无法编辑');
      }
    } else {
      // 创建模式：直接设置默认值并显示弹窗
      console.log('=== 创建模式 - 设置默认值 ===');
      
      // 重置表单和开关状态
      form.resetFields();
      setSwitchStates({
        enabled: true,
        block_on_input_risk: false,  // 默认不阻断
        block_on_output_risk: false, // 默认不阻断
        enable_reasoning_detection: true, // 默认开启
        stream_chunk_size: 50, // 默认每50个chunk检测一次
      });
      
      // 更新表单key并显示弹窗
      setFormKey(prev => prev + 1);
      setIsModalVisible(true);
    }
  };

  // 显示查看弹窗
  const showViewModal = (model: ProxyModel) => {
    setViewingModel(model);
    setIsViewModalVisible(true);
  };

  // 取消编辑 - 关闭弹窗并重置表单状态
  const handleCancel = () => {
    setIsModalVisible(false);
    setIsViewModalVisible(false);
    setEditingModel(null);
    setViewingModel(null);
    // 不要立即重置表单，等Modal动画完成后再重置
    setTimeout(() => {
      form.resetFields();
    }, 300);
  };

  // 成功后关闭弹窗
  const handleClose = () => {
    setIsModalVisible(false);
    setIsViewModalVisible(false);
    setEditingModel(null);
    setViewingModel(null);
    // 不要立即重置表单，等Modal动画完成后再重置
    setTimeout(() => {
      form.resetFields();
    }, 300);
  };

  // 检查代理模型名称是否重复
  const checkConfigNameDuplicate = (configName: string): boolean => {
    return models.some(model => 
      model.config_name === configName && 
      (!editingModel || model.id !== editingModel.id)
    );
  };

  // 自定义验证器：检查代理模型名称重复
  const validateConfigName = async (_: any, value: string) => {
    if (value && checkConfigNameDuplicate(value)) {
      throw new Error('代理模型名称已存在，请使用其他名称');
    }
  };

  // 自定义验证器：检查API Base URL格式
  const validateApiBaseUrl = async (_: any, value: string) => {
    if (value && !value.match(/^https?:\/\/.+/)) {
      throw new Error('API Base URL必须以http://或https://开头');
    }
  };

  // 保存模型配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      console.log('=== Switch状态 ===');
      console.log('switchStates:', switchStates);
      
      // 构造提交数据（极简配置）
      const formData: ProxyModelFormData = {
        config_name: values.config_name,
        api_base_url: values.api_base_url,
        model_name: values.model_name,
        enabled: switchStates.enabled,
        block_on_input_risk: switchStates.block_on_input_risk,
        block_on_output_risk: switchStates.block_on_output_risk,
        enable_reasoning_detection: switchStates.enable_reasoning_detection, // 使用实际配置
        stream_chunk_size: switchStates.stream_chunk_size,
      };

      // 编辑模式下，只有在用户输入了新的API Key时才包含在请求中
      if (!editingModel || (values.api_key && values.api_key.trim() !== '')) {
        formData.api_key = values.api_key;
      }
      
      console.log('=== 提交给后端的数据 ===');
      console.log('enabled:', formData.enabled, typeof formData.enabled);
      console.log('block_on_input_risk:', formData.block_on_input_risk, typeof formData.block_on_input_risk);
      console.log('block_on_output_risk:', formData.block_on_output_risk, typeof formData.block_on_output_risk);
      console.log('enable_reasoning_detection:', formData.enable_reasoning_detection, typeof formData.enable_reasoning_detection);

      const token = localStorage.getItem('auth_token');
      const headers = { Authorization: `Bearer ${token}` };

      if (editingModel) {
        // 编辑现有配置
        await axios.put(`/api/v1/proxy/models/${editingModel.id}`, formData, { headers });
        message.success('模型配置已更新');
      } else {
        // 创建新配置
        await axios.post('/api/v1/proxy/models', formData, { headers });
        message.success('模型配置已创建');
      }

      handleClose();
      fetchModels();
    } catch (error: any) {
      console.error('保存失败:', error);
      
      // 处理不同类型的错误
      if (error.response) {
        // 服务器返回的错误
        const errorMessage = error.response.data?.message || error.response.data?.error || '保存失败';
        if (error.response.status === 409 || errorMessage.includes('已存在') || errorMessage.includes('重复')) {
          message.error('代理模型名称已存在，请使用其他名称');
        } else {
          message.error(`保存失败：${errorMessage}`);
        }
      } else if (error.errorFields) {
        // 表单验证错误
        const firstError = error.errorFields[0];
        if (firstError && firstError.errors && firstError.errors.length > 0) {
          message.error(firstError.errors[0]);
        } else {
          message.error('请检查表单输入信息');
        }
      } else {
        // 其他错误
        message.error('保存失败，请检查网络连接或稍后重试');
      }
    }
  };

  // 删除模型配置
  const handleDelete = async (id: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.delete(`/api/v1/proxy/models/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data && response.data.success) {
        message.success('模型配置已删除');
        fetchModels();
      } else {
        const errorMessage = response.data?.error || '删除失败';
        message.error(errorMessage);
      }
    } catch (error: any) {
      console.error('删除失败:', error);
      
      // 处理不同类型的错误
      if (error.response) {
        const errorMessage = error.response.data?.error || error.response.data?.message || '删除失败';
        if (error.response.status === 404) {
          message.error('模型配置不存在或已被删除');
        } else if (error.response.status === 403) {
          message.error('无权限删除此模型配置');
        } else {
          message.error(`删除失败：${errorMessage}`);
        }
      } else if (error.request) {
        message.error('网络错误，请检查连接');
      } else {
        message.error('删除失败，请稍后重试');
      }
    }
  };

  const columns = [
    {
      title: '代理模型名称',
      dataIndex: 'config_name',
      key: 'config_name',
      render: (text: string, record: ProxyModel) => (
        <Space>
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {!record.enabled && <Tag color="red">已禁用</Tag>}
        </Space>
      ),
    },
    {
      title: '上游API模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
    },
    {
      title: '安全配置',
      key: 'security',
      render: (_: any, record: ProxyModel) => (
        <Space>
          {record.enable_reasoning_detection && <Tag color="purple">推理检测</Tag>}
          {record.block_on_input_risk && <Tag color="red">输入阻断</Tag>}
          {record.block_on_output_risk && <Tag color="orange">输出阻断</Tag>}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ProxyModel) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => showViewModal(record)}
          >
            查看
          </Button>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => showModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个模型配置吗？"
            description="删除后将无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card 
        title={
          <Space>
            <ApiOutlined />
            代理模型配置
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => showModal()}
          >
            添加模型
          </Button>
        }
      >
        <Table
          dataSource={models}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个模型配置`,
          }}
        />
      </Card>

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingModel ? '编辑模型配置' : '添加模型配置'}
        visible={isModalVisible}
        onOk={handleSave}
        onCancel={handleCancel}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          key={formKey}
          form={form}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            name="config_name"
            label="代理模型名称"
            rules={[
              { required: true, message: '请输入代理模型名称' },
              { validator: validateConfigName }
            ]}
            tooltip="用户在API调用中指定的模型名，建议使用 提供商-模型 格式"
          >
            <Input placeholder="如：aliyun-qwen-3, openai-gpt-4, claude-3-sonnet" />
          </Form.Item>


          <Form.Item
            name="api_base_url"
            label="上游API Base URL"
            rules={[
              { required: true, message: '请输入上游API Base URL' },
              { validator: validateApiBaseUrl }
            ]}
          >
            <Input placeholder="如：https://api.openai.com/v1" autoComplete="url" />
          </Form.Item>

          {/* 隐藏的用户名字段，防止浏览器将API Key识别为密码 */}
          <input 
            type="text" 
            name="username" 
            autoComplete="username" 
            style={{ position: 'absolute', left: '-9999px', opacity: 0 }} 
            tabIndex={-1}
            readOnly
          />

          <Form.Item
            name="api_key"
            label="上游API Key"
            rules={[{ required: !editingModel, message: '请输入上游API Key' }]}
            tooltip={editingModel ? "出于安全考虑，编辑时不显示原API Key。如需更换，请输入新的API Key；留空则保持原有配置不变。" : "请输入上游API的访问密钥"}
          >
            <Input.Password 
              placeholder={editingModel ? "留空保持原有API Key不变，或输入新的API Key" : "输入上游API Key"} 
              autoComplete="new-password"
              data-lpignore="true"
              data-form-type="other"
              visibilityToggle={false}
            />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="上游API模型名称"
            rules={[{ required: true, message: '请输入上游API模型名称' }]}
            tooltip="发送给上游模型API的实际模型名，必须与上游API支持的模型名一致"
          >
            <Input placeholder="如：gpt-4-turbo-preview、claude-3-5-sonnet-20241022" />
          </Form.Item>

          <Form.Item label="启用此配置">
            <Switch 
              checked={switchStates.enabled}
              onChange={(checked) => setSwitchStates(prev => ({ ...prev, enabled: checked }))}
            />
          </Form.Item>

          <div style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>安全配置</div>
            <div style={{ marginBottom: 8, color: '#666', fontSize: '14px' }}>
              输入检测和输出检测始终开启，为您提供全面安全防护
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.enable_reasoning_detection}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, enable_reasoning_detection: checked }))}
              /> 启用推理检测（检测模型的推理过程内容）
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.block_on_input_risk}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, block_on_input_risk: checked }))}
              /> 输入风险时阻断请求（默认只记录，不阻断）
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.block_on_output_risk}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, block_on_output_risk: checked }))}
              /> 输出风险时阻断响应（默认只记录，不阻断）
            </div>
          </div>

          <Form.Item 
            label="流式检测间隔" 
            tooltip="流式输出时，每N个chunk检测一次，范围1-500，默认50"
          >
            <Input 
              type="number"
              min={1}
              max={500}
              value={switchStates.stream_chunk_size}
              onChange={(e) => setSwitchStates(prev => ({ ...prev, stream_chunk_size: parseInt(e.target.value) || 50 }))}
              placeholder="输入检测间隔（默认50）"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看弹窗 */}
      <Modal
        title="查看模型配置"
        visible={isViewModalVisible}
        onCancel={handleCancel}
        footer={[
          <Button key="close" onClick={handleCancel}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {viewingModel && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="代理模型名称">{viewingModel.config_name}</Descriptions.Item>
            <Descriptions.Item label="上游API模型名称">{viewingModel.model_name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Space>
                {viewingModel.enabled ? 
                  <Tag color="green">已启用</Tag> : 
                  <Tag color="red">已禁用</Tag>
                }
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="安全配置">
              <Space direction="vertical">
                {viewingModel.enable_reasoning_detection && <Tag color="purple">推理检测</Tag>}
                {viewingModel.block_on_input_risk && <Tag color="red">输入阻断</Tag>}
                {viewingModel.block_on_output_risk && <Tag color="orange">输出阻断</Tag>}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(viewingModel.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default ProxyModelManagement;