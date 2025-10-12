import React, { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  message,
  Tag,
  Select,
  Upload,
  Card,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Alert
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { knowledgeBaseApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { KnowledgeBase, SimilarQuestionResult } from '../../types';
import ConfigSetSelector from '../../components/ConfigSetSelector';
import api from '../../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface ConfigTemplate {
  id: number;
  name: string;
  is_default: boolean;
}

const KnowledgeBaseManagement: React.FC = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<KnowledgeBase | null>(null);
  const [form] = Form.useForm();
  const [fileUploadLoading, setFileUploadLoading] = useState(false);
  const [fileReplaceModalVisible, setFileReplaceModalVisible] = useState(false);
  const [replacingKb, setReplacingKb] = useState<KnowledgeBase | null>(null);
  const [replaceForm] = Form.useForm();
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [searchingKb, setSearchingKb] = useState<KnowledgeBase | null>(null);
  const [searchResults, setSearchResults] = useState<SimilarQuestionResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchForm] = Form.useForm();
  const [configTemplates, setConfigTemplates] = useState<ConfigTemplate[]>([]);
  const [selectedConfigSet, setSelectedConfigSet] = useState<number | undefined>();
  const { user, onUserSwitch } = useAuth();

  const categories = [
    { value: 'S1', label: `S1 - ${t('category.S1')}` },
    { value: 'S2', label: `S2 - ${t('category.S2')}` },
    { value: 'S3', label: `S3 - ${t('category.S3')}` },
    { value: 'S4', label: `S4 - ${t('category.S4')}` },
    { value: 'S5', label: `S5 - ${t('category.S5')}` },
    { value: 'S6', label: `S6 - ${t('category.S6')}` },
    { value: 'S7', label: `S7 - ${t('category.S7')}` },
    { value: 'S8', label: `S8 - ${t('category.S8')}` },
    { value: 'S9', label: `S9 - ${t('category.S9')}` },
    { value: 'S10', label: `S10 - ${t('category.S10')}` },
    { value: 'S11', label: `S11 - ${t('category.S11')}` },
    { value: 'S12', label: `S12 - ${t('category.S12')}` },
  ];

  useEffect(() => {
    fetchData();
    fetchConfigTemplates();
  }, []);

  useEffect(() => {
    if (selectedConfigSet) {
      fetchData();
    }
  }, [selectedConfigSet]);

  // Listen to user switch event, automatically refresh data
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      fetchData();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Filter by selected config set if one is selected
      const params = selectedConfigSet ? { template_id: selectedConfigSet } : {};
      const result = await knowledgeBaseApi.list(params);
      setData(result);
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchConfigTemplates = async () => {
    try {
      const response = await api.get('/api/v1/config/risk-configs');
      setConfigTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching config templates:', error);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    // Pre-fill template_id with currently selected config set
    if (selectedConfigSet) {
      form.setFieldsValue({ template_id: selectedConfigSet });
    }
    setModalVisible(true);
  };

  const handleEdit = (record: KnowledgeBase) => {
    setEditingItem(record);
    form.setFieldsValue({
      category: record.category,
      name: record.name,
      description: record.description,
      is_active: record.is_active,
      is_global: record.is_global,
    });
    setModalVisible(true);
  };

  // Strict file content validation
  const validateTextFile = async (file: File): Promise<boolean> => {
    try {      
      const text = await file.text();

      if (!text.trim()) {
        message.error(t('knowledge.emptyFile'));
        return false;
      }

      const lines = text.trim().split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        message.error(t('knowledge.emptyFile'));
        return false;
      }

      // Strictly validate the first few lines (up to 5 lines)
      const linesToCheck = Math.min(5, lines.length);
      let validLines = 0;
      
      for (let i = 0; i < linesToCheck; i++) {
        const line = lines[i].trim();
        
        // Check if it is a JSON format
        if (!line.startsWith('{') || !line.endsWith('}')) {
          message.error(t('knowledge.formatError', { line: i + 1, error: t('knowledge.invalidJSON') }));
          return false;
        }

        try {
          const jsonObj = JSON.parse(line);

          // Check required fields
          if (!jsonObj.questionid || !jsonObj.question || !jsonObj.answer) {
            message.error(t('knowledge.missingFields', { line: i + 1 }));
            return false;
          }

          // Check field types
          if (typeof jsonObj.questionid !== 'string' ||
              typeof jsonObj.question !== 'string' ||
              typeof jsonObj.answer !== 'string') {
            message.error(t('knowledge.invalidFieldType', { line: i + 1 }));
            return false;
          }

          // Check content is not empty
          if (!jsonObj.question.trim() || !jsonObj.answer.trim()) {
            message.error(t('knowledge.emptyContent', { line: i + 1 }));
            return false;
          }

          validLines++;
        } catch (parseError: any) {
          message.error(t('knowledge.parseError', { line: i + 1, error: parseError.message }));
          return false;
        }
      }

      if (validLines === 0) {
        message.error(t('knowledge.noValidPairs'));
        return false;
      }

      message.success(t('knowledge.validationSuccess', { count: validLines }));
      return true;
    } catch (error) {
      message.error(t('knowledge.readFileFailed'));
      return false;
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingItem) {
        await knowledgeBaseApi.update(editingItem.id, values);
        message.success(t('common.updateSuccess'));
      } else {
        // Creating a knowledge base requires file upload
        if (!values.file || values.file.length === 0) {
          message.error(t('knowledge.selectFile'));
          return;
        }

        const file = values.file[0].originFileObj;
        
        // Validate file content
        const isValid = await validateTextFile(file);
        if (!isValid) {
          return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', values.category);
        formData.append('name', values.name);
        formData.append('description', values.description || '');
        formData.append('is_active', values.is_active ? 'true' : 'false');
        formData.append('is_global', values.is_global ? 'true' : 'false');

        setFileUploadLoading(true);
        await knowledgeBaseApi.create(formData);
        message.success(t('knowledge.uploadSuccess'));
      }

      setModalVisible(false);
      fetchData();
    } catch (error: any) {
      console.error('Error saving knowledge base:', error);
      message.error(error.response?.data?.detail || t('common.saveFailed'));
    } finally {
      setFileUploadLoading(false);
    }
  };

  const handleDelete = async (record: KnowledgeBase) => {
    try {
      await knowledgeBaseApi.delete(record.id);
      message.success(t('knowledge.deleteSuccess'));
      fetchData();
    } catch (error) {
      console.error('Error deleting knowledge base:', error);
      message.error(t('knowledge.deleteFailed'));
    }
  };

  const handleReplaceFile = (record: KnowledgeBase) => {
    setReplacingKb(record);
    replaceForm.resetFields();
    setFileReplaceModalVisible(true);
  };

  const handleFileReplace = async (values: any) => {
    if (!replacingKb || !values.file || values.file.length === 0) {
      message.error(t('knowledge.selectFile'));
      return;
    }

    const file = values.file[0].originFileObj;
    
    // Validate file content
    const isValid = await validateTextFile(file);
    if (!isValid) {
      return;
    }

    try {
      setFileUploadLoading(true);
      await knowledgeBaseApi.replaceFile(replacingKb.id, file);
      message.success(t('knowledge.replaceSuccess'));
      setFileReplaceModalVisible(false);
      fetchData();
    } catch (error: any) {
      console.error('Error replacing file:', error);
      message.error(error.response?.data?.detail || t('knowledge.replaceFailed'));
    } finally {
      setFileUploadLoading(false);
    }
  };

  const handleSearch = (record: KnowledgeBase) => {
    setSearchingKb(record);
    setSearchResults([]);
    searchForm.resetFields();
    setSearchModalVisible(true);
  };

  const handleSearchQuery = async (values: any) => {
    if (!searchingKb || !values.query.trim()) {
      message.error(t('knowledge.enterSearchContent'));
      return;
    }

    try {
      setSearchLoading(true);
      const results = await knowledgeBaseApi.search(searchingKb.id, values.query.trim(), 5);
      setSearchResults(results);
      if (results.length === 0) {
        message.info(t('knowledge.noSimilarQuestions'));
      }
    } catch (error: any) {
      console.error('Error searching knowledge base:', error);
      message.error(error.response?.data?.detail || t('knowledge.searchFailed'));
    } finally {
      setSearchLoading(false);
    }
  };

  const getCategoryLabel = (category: string) => {
    const item = categories.find(c => c.value === category);
    return item?.label || category;
  };

  const getFileName = (filePath: string) => {
    if (!filePath) return '-';
    // Extract file name from file path
    const parts = filePath.split('/');
    const fileName = parts[parts.length - 1];
    // Remove knowledge base ID prefix (kb_123_filename.jsonl -> filename.jsonl)
    const match = fileName.match(/^kb_\d+_(.+)$/);
    return match ? match[1] : fileName;
  };

  const getTemplateName = (templateId: number | null) => {
    if (!templateId) return t('common.none');
    const template = configTemplates.find(t => t.id === templateId);
    return template ? template.name : t('common.none');
  };


  const columns = [
    {
      title: t('results.category'),
      dataIndex: 'category',
      key: 'category',
      width: 180,
      render: (category: string) => (
        <Tag color="blue">
          {getCategoryLabel(category)}
        </Tag>
      ),
    },
    {
      title: t('knowledge.knowledgeBaseName'),
      dataIndex: 'name',
      key: 'name',
      width: 150,
      ellipsis: true,
    },
    {
      title: t('blacklist.configTemplate'),
      dataIndex: 'template_id',
      key: 'template_id',
      width: 150,
      render: (templateId: number | null) => (
        <Tag color={templateId ? 'blue' : 'default'}>
          {getTemplateName(templateId)}
        </Tag>
      ),
    },
    {
      title: t('common.description'),
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: t('knowledge.fileName'),
      dataIndex: 'file_path',
      key: 'file_name',
      width: 150,
      ellipsis: true,
      render: (filePath: string) => (
        <Tooltip title={getFileName(filePath)}>
          {getFileName(filePath)}
        </Tooltip>
      ),
    },
    {
      title: t('knowledge.qaPairsCount'),
      dataIndex: 'total_qa_pairs',
      key: 'total_qa_pairs',
      width: 100,
      align: 'center' as const,
      render: (count: number) => (
        <Tag color="green">{count}</Tag>
      ),
    },
    {
      title: t('common.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center' as const,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? t('common.enabled') : t('common.disabled')}
        </Tag>
      ),
    },
    {
      title: t('entityType.sourceColumn'),
      dataIndex: 'is_global',
      key: 'is_global',
      width: 100,
      align: 'center' as const,
      render: (isGlobal: boolean) => (
        <Tag color={isGlobal ? 'blue' : 'default'}>
          {isGlobal ? t('entityType.system') : t('entityType.custom')}
        </Tag>
      ),
    },
    {
      title: t('common.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: t('common.operation'),
      key: 'action',
      width: 300,
      fixed: 'right' as const,
      render: (_: any, record: KnowledgeBase) => (
        <Space size="small">
          <Tooltip title={t('knowledge.editBasicInfo')}>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            >
              {t('common.edit')}
            </Button>
          </Tooltip>
          <Tooltip title={t('knowledge.replaceKBFile')}>
            <Button
              type="link"
              size="small"
              icon={<UploadOutlined />}
              onClick={() => handleReplaceFile(record)}
            >
              {t('knowledge.replaceFile')}
            </Button>
          </Tooltip>
          <Tooltip title={t('knowledge.searchTest')}>
            <Button
              type="link"
              size="small"
              icon={<SearchOutlined />}
              onClick={() => handleSearch(record)}
            >
              {t('knowledge.searchTest')}
            </Button>
          </Tooltip>
          <Popconfirm
            title={t('knowledge.deleteConfirmKB', { name: record.name })}
            onConfirm={() => handleDelete(record)}
            okText={t('common.confirm')}
            cancelText={t('common.cancel')}
          >
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              {t('common.delete')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Config Set Filter */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            message={t('configSet.filterInfo') || 'Select a config set to view and manage its knowledge bases'}
            description={
              t('configSet.filterDescription') ||
              'You can filter knowledge bases by config set. Only knowledge bases belonging to the selected config set will be displayed.'
            }
            type="info"
            showIcon
            icon={<FilterOutlined />}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ minWidth: 120 }}>{t('configSet.selectConfigSet') || 'Config Set:'}  </span>
            <ConfigSetSelector
              value={selectedConfigSet}
              onChange={setSelectedConfigSet}
              allowCreate={true}
              style={{ flex: 1 }}
            />
          </div>
        </Space>
      </Card>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <h3>{t('knowledge.knowledgeBaseManagement')}</h3>
              <p style={{ color: '#666', margin: 0 }}>
                {t('knowledge.knowledgeBaseDescription')}
              </p>
            </Col>
            <Col>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAdd}
                disabled={!selectedConfigSet}
              >
                {t('knowledge.addKnowledgeBase')}
              </Button>
              {!selectedConfigSet && (
                <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                  {t('configSet.pleaseSelectFirst') || 'Please select a config set first'}
                </div>
              )}
            </Col>
          </Row>
        </div>

        <Alert
          message={t('knowledge.fileFormatDescription')}
          description={
            <div>
              <p>{t('knowledge.fileFormatDetails')}</p>
              <pre style={{ backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
{`{"questionid": "Unique question ID", "question": "Question content", "answer": "Answer content"}`}
              </pre>
              <p style={{ margin: 0 }}>
                <InfoCircleOutlined style={{ color: '#1890ff' }} />
                {t('knowledge.fileFormatNote')}
              </p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1500 }}
        />
      </Card>

      {/* Add/edit knowledge base modal */}
      <Modal
        title={editingItem ? t('knowledge.editKnowledgeBase') : t('knowledge.addKnowledgeBase')}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
        confirmLoading={fileUploadLoading}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="template_id"
            label={t('blacklist.configTemplate')}
            extra={t('blacklist.configTemplateExtra')}
          >
            <Select
              placeholder={t('blacklist.selectConfigTemplate')}
              allowClear
            >
              {configTemplates.map(template => (
                <Option key={template.id} value={template.id}>
                  {template.name}
                  {template.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>{t('protectionTemplate.default')}</Tag>}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="category"
            label={t('knowledge.riskCategory')}
            rules={[{ required: true, message: t('knowledge.selectRiskCategory') }]}
          >
            <Select placeholder={t('knowledge.selectRiskCategoryPlaceholder')}>
              {categories.map(category => (
                <Option key={category.value} value={category.value}>
                  {category.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label={t('knowledge.knowledgeBaseName')}
            rules={[{ required: true, message: t('knowledge.knowledgeBaseNameRequired') }]}
          >
            <Input placeholder={t('knowledge.knowledgeBaseNamePlaceholder')} />
          </Form.Item>

          <Form.Item
            name="description"
            label={t('common.description')}
          >
            <TextArea
              rows={3}
              placeholder={t('knowledge.descriptionPlaceholder')}
            />
          </Form.Item>

          {!editingItem && (
            <Form.Item
              name="file"
              label={t('knowledge.file')}
              rules={[{ required: true, message: t('knowledge.selectFile') }]}
              valuePropName="fileList"
              getValueFromEvent={(e) => {
                if (Array.isArray(e)) {
                  return e;
                }
                return e && e.fileList;
              }}
            >
              <Upload
                beforeUpload={() => false}
                accept="*"
                maxCount={1}
                showUploadList={{
                  showPreviewIcon: false,
                  showRemoveIcon: true,
                  showDownloadIcon: false
                }}
              >
                <Button icon={<UploadOutlined />}>{t('knowledge.chooseFile')}</Button>
              </Upload>
            </Form.Item>
          )}

          <Form.Item
            name="is_active"
            label={t('knowledge.enableStatus')}
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>

          {user?.is_super_admin && (
            <Form.Item
              name="is_global"
              label={
                <span>
                  {t('knowledge.globalKnowledgeBase')}
                  <Tooltip title={t('knowledge.globalKnowledgeBaseTooltip')}>
                    <InfoCircleOutlined style={{ marginLeft: 4 }} />
                  </Tooltip>
                </span>
              }
              valuePropName="checked"
              initialValue={false}
            >
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* Replace file modal */}
      <Modal
        title={t('knowledge.replaceFileTitle', { name: replacingKb?.name })}
        open={fileReplaceModalVisible}
        onCancel={() => {
          setFileReplaceModalVisible(false);
          replaceForm.resetFields();
        }}
        onOk={() => replaceForm.submit()}
        confirmLoading={fileUploadLoading}
      >
        <Alert
          message={t('knowledge.attention')}
          description={t('knowledge.replaceFileWarning')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form
          form={replaceForm}
          onFinish={handleFileReplace}
        >
          <Form.Item
            name="file"
            label={t('knowledge.selectNewFile')}
            rules={[{ required: true, message: t('knowledge.selectFile') }]}
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e;
              }
              return e && e.fileList;
            }}
          >
            <Upload
              beforeUpload={() => false}
              accept="*"
              maxCount={1}
              showUploadList={{
                showPreviewIcon: false,
                showRemoveIcon: true,
                showDownloadIcon: false
              }}
            >
              <Button icon={<UploadOutlined />}>{t('knowledge.chooseFile')}</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      {/* Search test modal */}
      <Modal
        title={t('knowledge.searchTestTitle', { name: searchingKb?.name })}
        open={searchModalVisible}
        onCancel={() => {
          setSearchModalVisible(false);
          searchForm.resetFields();
          setSearchResults([]);
        }}
        footer={null}
        width={800}
      >
        <Form 
          form={searchForm}
          onFinish={handleSearchQuery} 
          layout="inline" 
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            name="query"
            style={{ flex: 1 }}
            rules={[{ required: true, message: t('knowledge.searchContent') }]}
          >
            <Input placeholder={t('knowledge.searchPlaceholder')} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={searchLoading}>
              {t('common.search')}
            </Button>
          </Form.Item>
        </Form>

        {searchResults.length > 0 && (
          <div>
            <h4>{t('knowledge.searchResults')}</h4>
            {searchResults.map((result, index) => (
              <Card key={index} size="small" style={{ marginBottom: 8 }}>
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <Tag color="blue">{t('knowledge.similarity', { score: (result.similarity_score * 100).toFixed(1) })}</Tag>
                    <Tag color="green">{t('knowledge.rank', { rank: result.rank })}</Tag>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <strong>{t('knowledge.questionLabel')}</strong>{result.question}
                  </div>
                  <div>
                    <strong>{t('knowledge.answerLabel')}</strong>{result.answer}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default KnowledgeBaseManagement;