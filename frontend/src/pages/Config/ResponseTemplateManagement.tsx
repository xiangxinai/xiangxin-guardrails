import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, Space, message, Tag, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { configApi } from '../../services/api';
import type { ResponseTemplate } from '../../types';

const { TextArea } = Input;
const { Option } = Select;

const ResponseTemplateManagement: React.FC = () => {
  const [data, setData] = useState<ResponseTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<ResponseTemplate | null>(null);
  const [form] = Form.useForm();

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
    { value: 'default', label: '默认模板' },
  ];

  const riskLevels = [
    { value: '高风险', label: '高风险' },
    { value: '中风险', label: '中风险' },
    { value: '低风险', label: '低风险' },
    { value: '无风险', label: '无风险' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const result = await configApi.responses.list();
      setData(result);
    } catch (error) {
      console.error('Error fetching response templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: ResponseTemplate) => {
    setEditingItem(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  // 根据类别自动确定风险等级
  const getCategoryRiskLevel = (category: string) => {
    const highRiskCategories = ['S2', 'S3', 'S5', 'S9'];
    const mediumRiskCategories = ['S1', 'S4', 'S6', 'S7'];
    const lowRiskCategories = ['S8', 'S10', 'S11', 'S12'];
    
    if (highRiskCategories.includes(category)) {
      return '高风险';
    } else if (mediumRiskCategories.includes(category)) {
      return '中风险';
    } else if (lowRiskCategories.includes(category)) {
      return '低风险';
    } else {
      return '无风险'; // default category
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      // 自动设置风险等级
      const submissionData = {
        ...values,
        risk_level: getCategoryRiskLevel(values.category)
      };

      if (editingItem) {
        await configApi.responses.update(editingItem.id, submissionData);
        message.success('更新成功');
      } else {
        await configApi.responses.create(submissionData);
        message.success('创建成功');
      }

      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error saving response template:', error);
      message.error('保存失败，请重试');
    }
  };

  const handleDelete = async (record: ResponseTemplate) => {
    try {
      await configApi.responses.delete(record.id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Error deleting response template:', error);
      message.error('删除失败，请重试');
    }
  };

  const handleToggleStatus = async (record: ResponseTemplate) => {
    try {
      await configApi.responses.update(record.id, {
        category: record.category,
        risk_level: record.risk_level,
        template_content: record.template_content,
        is_default: record.is_default,
        is_active: !record.is_active
      });
      message.success(`${!record.is_active ? '启用' : '禁用'}成功`);
      fetchData();
    } catch (error) {
      console.error('Error toggling template status:', error);
      message.error('操作失败，请重试');
    }
  };

  const getCategoryLabel = (category: string) => {
    const item = categories.find(c => c.value === category);
    return item?.label || category;
  };

  const getRiskLevelLabel = (level: string) => {
    const item = riskLevels.find(r => r.value === level);
    return item?.label || level;
  };

  const columns = [
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === 'default' ? 'blue' : 'orange'}>
          {getCategoryLabel(category)}
        </Tag>
      ),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => {
        const color = level === '高风险' ? 'red' : level === '中风险' ? 'orange' : level === '低风险' ? 'yellow' : 'green';
        return (
          <Tag color={color}>
            {getRiskLevelLabel(level)}
          </Tag>
        );
      },
    },
    {
      title: '代答内容',
      dataIndex: 'template_content',
      key: 'template_content',
      ellipsis: true,
      width: 300,
    },
    {
      title: '默认模板',
      dataIndex: 'is_default',
      key: 'is_default',
      render: (isDefault: boolean) => (
        <Tag color={isDefault ? 'green' : 'default'}>
          {isDefault ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: ResponseTemplate) => (
        <Space>
          <Tag color={active ? 'green' : 'red'}>
            {active ? '启用' : '禁用'}
          </Tag>
          <Button
            type="link"
            size="small"
            onClick={() => handleToggleStatus(record)}
          >
            {active ? '禁用' : '启用'}
          </Button>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ResponseTemplate) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              if (confirm(`确定要删除代答模板"${getCategoryLabel(record.category)}"吗？`)) {
                handleDelete(record);
              }
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
        >
          添加代答模板
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingItem ? '编辑代答模板' : '添加代答模板'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
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
            name="template_content"
            label="代答内容"
            rules={[{ required: true, message: '请输入代答内容' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入代答内容"
            />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="设为默认模板"
            valuePropName="checked"
            initialValue={false}
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ResponseTemplateManagement;