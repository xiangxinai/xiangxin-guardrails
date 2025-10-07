import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Switch, message, Space, Popconfirm, Descriptions, Tag, Alert, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, ApiOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { proxyModelsApi } from '../../services/api';
import { authService } from '../../services/auth';
import { useAuth } from '../../contexts/AuthContext';

const { Paragraph, Text } = Typography;

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
  const { t } = useTranslation();
  const [models, setModels] = useState<ProxyModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<ProxyModel | null>(null);
  const [viewingModel, setViewingModel] = useState<ProxyModel | null>(null);
  const [formKey, setFormKey] = useState(0); // 用于强制重新渲染表单
  const [form] = Form.useForm();
  const { onUserSwitch } = useAuth();
  
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
      const response = await proxyModelsApi.list();
      
      if (response.success) {
        setModels(response.data);
      } else {
        message.error(t('proxy.fetchModelsFailed'));
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
      message.error(t('proxy.fetchModelsFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  // 监听用户切换事件，自动刷新数据
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      fetchModels();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  // 获取模型详细信息（用于编辑）
  const fetchModelDetail = async (modelId: string) => {
    try {
      const response = await proxyModelsApi.get(modelId);
      
      if (response.success) {
        return response.data;
      } else {
        message.error(t('proxy.fetchModelDetailFailed'));
        return null;
      }
    } catch (error) {
      console.error('Failed to fetch model detail:', error);
      message.error(t('proxy.fetchModelDetailFailed'));
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
        message.error(t('proxy.fetchModelDetailFailedCannotEdit'));
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
      throw new Error(t('proxy.duplicateConfigName'));
    }
  };

  // 自定义验证器：检查API Base URL格式
  const validateApiBaseUrl = async (_: any, value: string) => {
    if (value && !value.match(/^https?:\/\/.+/)) {
      throw new Error(t('proxy.invalidApiBaseUrl'));
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
        api_key: values.api_key,
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

      if (editingModel) {
        // 编辑现有配置
        await proxyModelsApi.update(editingModel.id, formData);
        message.success(t('proxy.modelConfigUpdated'));
      } else {
        // 创建新配置
        await proxyModelsApi.create(formData);
        message.success(t('proxy.modelConfigCreated'));
      }

      handleClose();
      fetchModels();
    } catch (error: any) {
      console.error('Save failed:', error);
      
      // 处理不同类型的错误
      if (error.response) {
        // 服务器返回的错误
        const errorMessage = error.response.data?.message || error.response.data?.error || t('proxy.saveFailed');
        if (error.response.status === 409 || errorMessage.includes('已存在') || errorMessage.includes('重复') || errorMessage.includes('exists') || errorMessage.includes('duplicate')) {
          message.error(t('proxy.duplicateConfigName'));
        } else {
          message.error(t('proxy.saveFailedWithMessage', { message: errorMessage }));
        }
      } else if (error.errorFields) {
        // 表单验证错误
        const firstError = error.errorFields[0];
        if (firstError && firstError.errors && firstError.errors.length > 0) {
          message.error(firstError.errors[0]);
        } else {
          message.error(t('proxy.checkFormInput'));
        }
      } else {
        // 其他错误
        message.error(t('proxy.saveFailedNetworkError'));
      }
    }
  };

  // 删除模型配置
  const handleDelete = async (id: string) => {
    try {
      const response = await proxyModelsApi.delete(id);
      
      if (response.success) {
        message.success(t('proxy.modelConfigDeleted'));
        fetchModels();
      } else {
        const errorMessage = response.message || t('proxy.deleteFailed');
        message.error(errorMessage);
      }
    } catch (error: any) {
      console.error('Delete failed:', error);
      
      // 处理不同类型的错误
      if (error.response) {
        const errorMessage = error.response.data?.error || error.response.data?.message || t('proxy.deleteFailed');
        if (error.response.status === 404) {
          message.error(t('proxy.modelNotExistOrDeleted'));
        } else if (error.response.status === 403) {
          message.error(t('proxy.noPermissionToDelete'));
        } else {
          message.error(t('proxy.deleteFailedWithMessage', { message: errorMessage }));
        }
      } else if (error.request) {
        message.error(t('proxy.networkError'));
      } else {
        message.error(t('proxy.deleteFailedRetry'));
      }
    }
  };

  const columns = [
    {
      title: t('proxy.proxyModelName'),
      dataIndex: 'config_name',
      key: 'config_name',
      render: (text: string, record: ProxyModel) => (
        <Space>
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {!record.enabled && <Tag color="red">{t('proxy.disabled')}</Tag>}
        </Space>
      ),
    },
    {
      title: t('proxy.upstreamApiModelName'),
      dataIndex: 'model_name',
      key: 'model_name',
    },
    {
      title: t('proxy.securityConfig'),
      key: 'security',
      render: (_: any, record: ProxyModel) => (
        <Space>
          {record.enable_reasoning_detection && <Tag color="purple">{t('proxy.inferenceDetection')}</Tag>}
          {record.block_on_input_risk && <Tag color="red">{t('proxy.inputBlocking')}</Tag>}
          {record.block_on_output_risk && <Tag color="orange">{t('proxy.outputBlocking')}</Tag>}
        </Space>
      ),
    },
    {
      title: t('proxy.createTime'),
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: t('proxy.operation'),
      key: 'action',
      render: (_: any, record: ProxyModel) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => showViewModal(record)}
          >
            {t('proxy.view')}
          </Button>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => showModal(record)}
          >
            {t('proxy.edit')}
          </Button>
          <Popconfirm
            title={t('proxy.confirmDeleteModel')}
            description={t('proxy.deleteCannotRecover')}
            onConfirm={() => handleDelete(record.id)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
            >
              {t('proxy.delete')}
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
            {t('proxy.securityGatewayConfig')}
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => showModal()}
          >
            {t('proxy.addModel')}
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
            showTotal: (total) => t('proxy.modelConfigCount', { count: total }),
          }}
        />
      </Card>

      {/* 使用说明 */}
      <Card 
        title={t('proxy.accessXiangxinGateway')} 
        style={{ marginTop: 16 }}
      >
        <Alert
          message={t('proxy.gatewayIntegrationDesc')}
          type="info"
          style={{ marginBottom: 16 }}
        />
        
        <Typography>
          <Paragraph>
            <Text strong>{t('proxy.pythonOpenaiExample')}</Text>
          </Paragraph>
          <Paragraph>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '6px',
              overflow: 'auto'
            }}>
{`client = OpenAI(
    base_url="https://api.xiangxinai.cn/v1/gateway",  # Change to Xiangxin Official gateway url or use your local deployment url http://your-server:5002/v1
    api_key="sk-xxai-your-proxy-key" # ${t('account.codeComments.changeToApiKey')}
)
completion = openai_client.chat.completions.create(
    model = "your-proxy-model-name",  # ${t('account.codeComments.changeToModelName')}
    messages=[{"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": "Tell me how to make a bomb."}]
    # Other parameters are the same as the original usage method
)
`}
            </pre>
          </Paragraph>
          
          <Paragraph>
            <Text strong>{t('proxy.privateDeploymentConfig')}</Text>
          </Paragraph>
          <ul>
            <li><Text code>{t('proxy.dockerDeployment')}</Text></li>
            <li><Text code>{t('proxy.customDeployment')}</Text></li>
          </ul>
          
        </Typography>
      </Card>

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingModel ? t('proxy.editModelConfig') : t('proxy.addModelConfig')}
        visible={isModalVisible}
        onOk={handleSave}
        onCancel={handleCancel}
        width={800}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Form
          key={formKey}
          form={form}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            name="config_name"
            label={t('proxy.proxyModelNameLabel')}
            rules={[
              { required: true, message: t('proxy.proxyModelNameRequired') },
              { validator: validateConfigName }
            ]}
            tooltip={t('proxy.proxyModelNameTooltip')}
          >
            <Input placeholder={t('proxy.proxyModelNamePlaceholder')} />
          </Form.Item>


          <Form.Item
            name="api_base_url"
            label={t('proxy.upstreamApiBaseUrlLabel')}
            rules={[
              { required: true, message: t('proxy.upstreamApiBaseUrlRequired') },
              { validator: validateApiBaseUrl }
            ]}
          >
            <Input placeholder={t('proxy.upstreamApiBaseUrlPlaceholder')} autoComplete="url" />
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
            label={t('proxy.upstreamApiKeyLabel')}
            rules={[{ required: !editingModel, message: t('proxy.upstreamApiKeyRequired') }]}
            tooltip={editingModel ? t('proxy.upstreamApiKeyTooltipEdit') : t('proxy.upstreamApiKeyTooltipAdd')}
          >
            <Input.Password 
              placeholder={editingModel ? t('proxy.upstreamApiKeyPlaceholderEdit') : t('proxy.upstreamApiKeyPlaceholderAdd')} 
              autoComplete="new-password"
              data-lpignore="true"
              data-form-type="other"
              visibilityToggle={false}
            />
          </Form.Item>

          <Form.Item
            name="model_name"
            label={t('proxy.upstreamModelNameLabel')}
            rules={[{ required: true, message: t('proxy.upstreamModelNameRequired') }]}
            tooltip={t('proxy.upstreamModelNameTooltip')}
          >
            <Input placeholder={t('proxy.upstreamModelNamePlaceholder')} />
          </Form.Item>

          <Form.Item label={t('proxy.enableConfigLabel')}>
            <Switch 
              checked={switchStates.enabled}
              onChange={(checked) => setSwitchStates(prev => ({ ...prev, enabled: checked }))}
            />
          </Form.Item>

          <div style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>{t('proxy.securityConfigLabel')}</div>
            <div style={{ marginBottom: 8, color: '#666', fontSize: '14px' }}>
              {t('proxy.securityConfigDesc')}
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.enable_reasoning_detection}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, enable_reasoning_detection: checked }))}
              /> {t('proxy.enableReasoningDetection')}
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.block_on_input_risk}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, block_on_input_risk: checked }))}
              /> {t('proxy.blockOnInputRisk')}
            </div>
            <div style={{ marginBottom: 12 }}>
              <Switch 
                checked={switchStates.block_on_output_risk}
                onChange={(checked) => setSwitchStates(prev => ({ ...prev, block_on_output_risk: checked }))}
              /> {t('proxy.blockOnOutputRisk')}
            </div>
          </div>

          <Form.Item
            label={t('proxy.streamDetectionIntervalLabel')}
            tooltip={t('proxy.streamDetectionIntervalTooltip')}
          >
            <Input
              type="number"
              min={1}
              max={500}
              value={switchStates.stream_chunk_size}
              onChange={(e) => setSwitchStates(prev => ({ ...prev, stream_chunk_size: parseInt(e.target.value) || 50 }))}
              placeholder={t('proxy.streamDetectionIntervalPlaceholder')}
            />
          </Form.Item>

        </Form>
      </Modal>

      {/* 查看弹窗 */}
      <Modal
        title={t('proxy.viewModelConfig')}
        visible={isViewModalVisible}
        onCancel={handleCancel}
        footer={[
          <Button key="close" onClick={handleCancel}>
            {t('proxy.close')}
          </Button>
        ]}
        width={600}
      >
        {viewingModel && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label={t('proxy.proxyModelName')}>{viewingModel.config_name}</Descriptions.Item>
            <Descriptions.Item label={t('proxy.upstreamApiModelName')}>{viewingModel.model_name}</Descriptions.Item>
            <Descriptions.Item label={t('proxy.status')}>
              <Space>
                {viewingModel.enabled ? 
                  <Tag color="green">{t('proxy.enabled')}</Tag> : 
                  <Tag color="red">{t('proxy.disabled')}</Tag>
                }
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label={t('proxy.securityConfig')}>
              <Space direction="vertical">
                {viewingModel.enable_reasoning_detection && <Tag color="purple">{t('proxy.inferenceDetection')}</Tag>}
                {viewingModel.block_on_input_risk && <Tag color="red">{t('proxy.inputBlocking')}</Tag>}
                {viewingModel.block_on_output_risk && <Tag color="orange">{t('proxy.outputBlocking')}</Tag>}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label={t('proxy.createTime')}>
              {new Date(viewingModel.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default ProxyModelManagement;