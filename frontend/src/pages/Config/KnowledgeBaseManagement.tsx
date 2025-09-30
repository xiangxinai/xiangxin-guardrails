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
  InfoCircleOutlined
} from '@ant-design/icons';
import { knowledgeBaseApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { KnowledgeBase, SimilarQuestionResult } from '../../types';

const { TextArea } = Input;
const { Option } = Select;

const KnowledgeBaseManagement: React.FC = () => {
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
  const { user, onUserSwitch } = useAuth();

  const categories = [
    { value: 'S1', label: 'S1 - 一般政治话题' },
    { value: 'S2', label: 'S2 - 敏感政治话题' },
    { value: 'S3', label: 'S3 - 损害国家形象' },
    { value: 'S4', label: 'S4 - 伤害未成年人' },
    { value: 'S5', label: 'S5 - 暴力犯罪' },
    { value: 'S6', label: 'S6 - 违法犯罪' },
    { value: 'S7', label: 'S7 - 色情' },
    { value: 'S8', label: 'S8 - 歧视内容' },
    { value: 'S9', label: 'S9 - 提示词攻击' },
    { value: 'S10', label: 'S10 - 辱骂' },
    { value: 'S11', label: 'S11 - 侵犯个人隐私' },
    { value: 'S12', label: 'S12 - 商业违法违规' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  // 监听用户切换事件，自动刷新数据
  useEffect(() => {
    const unsubscribe = onUserSwitch(() => {
      fetchData();
    });
    return unsubscribe;
  }, [onUserSwitch]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const result = await knowledgeBaseApi.list();
      setData(result);
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
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

  // 严格的文件内容验证
  const validateTextFile = async (file: File): Promise<boolean> => {
    try {
      // 打印文件信息用于调试
      console.log('=== 文件调试信息 ===');
      console.log('file.name:', file.name);
      console.log('file.type:', file.type);
      console.log('file.size:', file.size);
      console.log('file.lastModified:', new Date(file.lastModified));
      console.log('==================');
      
      const text = await file.text();
      
      if (!text.trim()) {
        message.error('文件内容为空');
        return false;
      }

      const lines = text.trim().split('\n').filter(line => line.trim());
      
      if (lines.length === 0) {
        message.error('文件内容为空');
        return false;
      }

      // 严格验证前几行（最多检查前5行）
      const linesToCheck = Math.min(5, lines.length);
      let validLines = 0;
      
      for (let i = 0; i < linesToCheck; i++) {
        const line = lines[i].trim();
        
        // 检查是否为JSON格式
        if (!line.startsWith('{') || !line.endsWith('}')) {
          message.error(`文件格式错误：第${i + 1}行不是有效的JSON格式`);
          return false;
        }
        
        try {
          const jsonObj = JSON.parse(line);
          
          // 检查必需字段
          if (!jsonObj.questionid || !jsonObj.question || !jsonObj.answer) {
            message.error(`文件格式错误：第${i + 1}行缺少必需字段 (questionid, question, answer)`);
            return false;
          }
          
          // 检查字段类型
          if (typeof jsonObj.questionid !== 'string' || 
              typeof jsonObj.question !== 'string' || 
              typeof jsonObj.answer !== 'string') {
            message.error(`文件格式错误：第${i + 1}行字段类型不正确，所有字段必须为字符串`);
            return false;
          }
          
          // 检查内容不为空
          if (!jsonObj.question.trim() || !jsonObj.answer.trim()) {
            message.error(`文件格式错误：第${i + 1}行问题或答案内容为空`);
            return false;
          }
          
          validLines++;
        } catch (parseError: any) {
          message.error(`文件格式错误：第${i + 1}行JSON解析失败 - ${parseError.message}`);
          return false;
        }
      }
      
      if (validLines === 0) {
        message.error('文件格式错误：未找到有效的问答对');
        return false;
      }
      
      message.success(`文件格式验证通过，检查了前${validLines}行`);
      return true;
    } catch (error) {
      message.error('文件读取失败');
      return false;
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingItem) {
        await knowledgeBaseApi.update(editingItem.id, values);
        message.success('更新成功');
      } else {
        // 创建知识库需要文件上传
        if (!values.file || values.file.length === 0) {
          message.error('请选择文件');
          return;
        }

        const file = values.file[0].originFileObj;
        
        // 额外调试信息 - 提交时的所有表单数据
        console.log('=== 提交时完整表单调试信息 ===');
        console.log('完整的 values:', values);
        console.log('values.category:', values.category);
        console.log('values.name:', values.name);
        console.log('values.description:', values.description);
        console.log('values.is_active:', values.is_active);
        console.log('values.file:', values.file);
        console.log('values.file[0]:', values.file[0]);
        console.log('values.file[0].name:', values.file[0].name);
        console.log('values.file[0].type:', values.file[0].type);
        console.log('originFileObj:', file);
        console.log('originFileObj.name:', file.name);
        console.log('originFileObj.type:', file.type);
        console.log('===============================');
        
        // 验证文件内容
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
        
        // 调试 FormData 内容
        console.log('=== FormData 调试信息 ===');
        console.log('FormData entries:');
        for (const [key, value] of formData.entries()) {
          console.log(`${key}:`, value);
        }
        console.log('=======================');

        setFileUploadLoading(true);
        await knowledgeBaseApi.create(formData);
        message.success('创建成功');
      }

      setModalVisible(false);
      fetchData();
    } catch (error: any) {
      console.error('Error saving knowledge base:', error);
      message.error(error.response?.data?.detail || '保存失败，请重试');
    } finally {
      setFileUploadLoading(false);
    }
  };

  const handleDelete = async (record: KnowledgeBase) => {
    try {
      await knowledgeBaseApi.delete(record.id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Error deleting knowledge base:', error);
      message.error('删除失败，请重试');
    }
  };

  const handleReplaceFile = (record: KnowledgeBase) => {
    setReplacingKb(record);
    replaceForm.resetFields();
    setFileReplaceModalVisible(true);
  };

  const handleFileReplace = async (values: any) => {
    if (!replacingKb || !values.file || values.file.length === 0) {
      message.error('请选择文件');
      return;
    }

    const file = values.file[0].originFileObj;
    
    // 额外调试信息 - 替换文件时的文件信息
    console.log('=== 替换文件时调试信息 ===');
    console.log('values.file[0].name:', values.file[0].name);
    console.log('values.file[0].type:', values.file[0].type);
    console.log('originFileObj.name:', file.name);
    console.log('originFileObj.type:', file.type);
    console.log('==========================');
    
    // 验证文件内容
    const isValid = await validateTextFile(file);
    if (!isValid) {
      return;
    }

    try {
      setFileUploadLoading(true);
      await knowledgeBaseApi.replaceFile(replacingKb.id, file);
      message.success('文件替换成功');
      setFileReplaceModalVisible(false);
      fetchData();
    } catch (error: any) {
      console.error('Error replacing file:', error);
      message.error(error.response?.data?.detail || '文件替换失败，请重试');
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
      message.error('请输入搜索内容');
      return;
    }

    try {
      setSearchLoading(true);
      const results = await knowledgeBaseApi.search(searchingKb.id, values.query.trim(), 5);
      setSearchResults(results);
      if (results.length === 0) {
        message.info('未找到相似的问题');
      }
    } catch (error: any) {
      console.error('Error searching knowledge base:', error);
      message.error(error.response?.data?.detail || '搜索失败，请重试');
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
    // 从文件路径中提取文件名
    const parts = filePath.split('/');
    const fileName = parts[parts.length - 1];
    // 移除知识库ID前缀 (kb_123_filename.jsonl -> filename.jsonl)
    const match = fileName.match(/^kb_\d+_(.+)$/);
    return match ? match[1] : fileName;
  };


  const columns = [
    {
      title: '类别',
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
      title: '知识库名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '文件名',
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
      title: '问答对数量',
      dataIndex: 'total_qa_pairs',
      key: 'total_qa_pairs',
      width: 100,
      align: 'center' as const,
      render: (count: number) => (
        <Tag color="green">{count}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center' as const,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '作用范围',
      dataIndex: 'is_global',
      key: 'is_global',
      width: 100,
      align: 'center' as const,
      render: (isGlobal: boolean) => (
        <Tag color={isGlobal ? 'purple' : 'default'}>
          {isGlobal ? '全局' : '个人'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right' as const,
      render: (_: any, record: KnowledgeBase) => (
        <Space size="small">
          <Tooltip title="编辑基本信息">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            >
              编辑
            </Button>
          </Tooltip>
          <Tooltip title="替换知识库文件">
            <Button
              type="link"
              size="small"
              icon={<UploadOutlined />}
              onClick={() => handleReplaceFile(record)}
            >
              替换文件
            </Button>
          </Tooltip>
          <Tooltip title="搜索测试">
            <Button
              type="link"
              size="small"
              icon={<SearchOutlined />}
              onClick={() => handleSearch(record)}
            >
              搜索测试
            </Button>
          </Tooltip>
          <Popconfirm
            title={`确定要删除知识库"${record.name}"吗？`}
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              size="small"
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
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <h3>代答知识库管理</h3>
              <p style={{ color: '#666', margin: 0 }}>
                管理各风险类别的问答对知识库，支持向量相似度搜索
              </p>
            </Col>
            <Col>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAdd}
              >
                添加知识库
              </Button>
            </Col>
          </Row>
        </div>

        <Alert
          message="文件格式说明"
          description={
            <div>
              <p>上传文本文件，每行一个 JSON 对象，包含以下字段：</p>
              <pre style={{ backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
{`{"questionid": "唯一问题ID", "question": "问题内容", "answer": "回答内容"}`}
              </pre>
              <p style={{ margin: 0 }}>
                <InfoCircleOutlined style={{ color: '#1890ff' }} />
                系统会自动验证文件内容，支持任何扩展名的文本文件。检测到风险时，会先在知识库中搜索相似问题，找到则返回对应答案。
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

      {/* 添加/编辑知识库弹窗 */}
      <Modal
        title={editingItem ? '编辑知识库' : '添加知识库'}
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
            name="category"
            label="风险类别"
            rules={[{ required: true, message: '请选择风险类别' }]}
          >
            <Select placeholder="请选择风险类别">
              {categories.map(category => (
                <Option key={category.value} value={category.value}>
                  {category.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入知识库描述（可选）"
            />
          </Form.Item>

          {!editingItem && (
            <Form.Item
              name="file"
              label="文件"
              rules={[{ required: true, message: '请选择文件' }]}
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
                onChange={(info) => {
                  console.log('=== Upload onChange 调试信息 ===');
                  if (info.fileList.length > 0) {
                    const file = info.fileList[0];
                    console.log('Upload file.name:', file.name);
                    console.log('Upload file.type:', file.type);
                    if (file.originFileObj) {
                      console.log('Upload originFileObj.name:', file.originFileObj.name);
                      console.log('Upload originFileObj.type:', file.originFileObj.type);
                    }
                  }
                  console.log('================================');
                }}
              >
                <Button icon={<UploadOutlined />}>选择文件</Button>
              </Upload>
            </Form.Item>
          )}

          <Form.Item
            name="is_active"
            label="启用状态"
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
                  全局知识库
                  <Tooltip title="全局知识库将对所有用户生效，只有管理员可以设置">
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

      {/* 替换文件弹窗 */}
      <Modal
        title={`替换知识库文件 - ${replacingKb?.name}`}
        open={fileReplaceModalVisible}
        onCancel={() => {
          setFileReplaceModalVisible(false);
          replaceForm.resetFields();
        }}
        onOk={() => replaceForm.submit()}
        confirmLoading={fileUploadLoading}
      >
        <Alert
          message="注意"
          description="替换文件将会删除原有的问答对和向量索引，并重新生成。此操作不可撤销。"
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
            label="选择新文件"
            rules={[{ required: true, message: '请选择文件' }]}
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
              onChange={(info) => {
                console.log('=== Replace Upload onChange 调试信息 ===');
                if (info.fileList.length > 0) {
                  const file = info.fileList[0];
                  console.log('Replace Upload file.name:', file.name);
                  console.log('Replace Upload file.type:', file.type);
                  if (file.originFileObj) {
                    console.log('Replace Upload originFileObj.name:', file.originFileObj.name);
                    console.log('Replace Upload originFileObj.type:', file.originFileObj.type);
                  }
                }
                console.log('==========================================');
              }}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      {/* 搜索测试弹窗 */}
      <Modal
        title={`搜索测试 - ${searchingKb?.name}`}
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
            rules={[{ required: true, message: '请输入搜索内容' }]}
          >
            <Input placeholder="请输入要搜索的问题" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={searchLoading}>
              搜索
            </Button>
          </Form.Item>
        </Form>

        {searchResults.length > 0 && (
          <div>
            <h4>搜索结果：</h4>
            {searchResults.map((result, index) => (
              <Card key={index} size="small" style={{ marginBottom: 8 }}>
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <Tag color="blue">相似度: {(result.similarity_score * 100).toFixed(1)}%</Tag>
                    <Tag color="green">排名: {result.rank}</Tag>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <strong>问题：</strong>{result.question}
                  </div>
                  <div>
                    <strong>回答：</strong>{result.answer}
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