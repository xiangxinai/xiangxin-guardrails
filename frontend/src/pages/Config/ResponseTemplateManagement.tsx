import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, message, Tag, Select } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { configApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import type { ResponseTemplate } from '../../types';

const { TextArea } = Input;
const { Option } = Select;

const ResponseTemplateManagement: React.FC = () => {
  const [data, setData] = useState<ResponseTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<ResponseTemplate | null>(null);
  const [form] = Form.useForm();
  const { onUserSwitch } = useAuth();

  const categories = [
    { value: 'S1', label: 'S1 - 一般政治话题', riskLevel: '中风险' },
    { value: 'S2', label: 'S2 - 敏感政治话题', riskLevel: '高风险' },
    { value: 'S3', label: 'S3 - 损害国家形象', riskLevel: '高风险' },
    { value: 'S4', label: 'S4 - 伤害未成年人', riskLevel: '中风险' },
    { value: 'S5', label: 'S5 - 暴力犯罪', riskLevel: '高风险' },
    { value: 'S6', label: 'S6 - 违法犯罪', riskLevel: '中风险' },
    { value: 'S7', label: 'S7 - 色情', riskLevel: '中风险' },
    { value: 'S8', label: 'S8 - 歧视内容', riskLevel: '低风险' },
    { value: 'S9', label: 'S9 - 提示词攻击', riskLevel: '高风险' },
    { value: 'S10', label: 'S10 - 辱骂', riskLevel: '低风险' },
    { value: 'S11', label: 'S11 - 侵犯个人隐私', riskLevel: '低风险' },
    { value: 'S12', label: 'S12 - 商业违法违规', riskLevel: '低风险' },
    { value: 'default', label: '默认拒答', riskLevel: '无风险' },
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
      const result = await configApi.responses.list();
      
      // 确保每个类别都有一条拒答记录，如果没有则创建默认的
      const existingCategories = result.map((item: ResponseTemplate) => item.category);
      const missingCategories = categories.filter(cat => !existingCategories.includes(cat.value));
      
      // 为缺失的类别创建默认拒答内容
      for (const category of missingCategories) {
        const defaultContent = `很抱歉，我不能回答关于${category.label.split(' - ')[1]}的问题。如有其他疑问，请联系客服。`;
        try {
          await configApi.responses.create({
            category: category.value,
            risk_level: category.riskLevel,
            template_content: defaultContent,
            is_default: true,
            is_active: true
          });
        } catch (error) {
          console.error(`Failed to create default template for ${category.value}:`, error);
        }
      }
      
      // 重新获取数据
      const updatedResult = await configApi.responses.list();
      setData(updatedResult);
    } catch (error) {
      console.error('Error fetching response templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record: ResponseTemplate) => {
    setEditingItem(record);
    form.setFieldsValue({
      category: record.category,
      template_content: record.template_content
    });
    setModalVisible(true);
  };


  const handleSubmit = async (values: any) => {
    try {
      if (!editingItem) {
        message.error('无效的编辑操作');
        return;
      }

      // 更新拒答内容，保持原有的类别和风险等级
      const submissionData = {
        category: editingItem.category,
        risk_level: editingItem.risk_level,
        template_content: values.template_content,
        is_default: true,
        is_active: true
      };

      await configApi.responses.update(editingItem.id, submissionData);
      message.success('拒答内容更新成功');

      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Error updating reject response:', error);
      message.error('更新失败，请重试');
    }
  };

  const getCategoryLabel = (category: string) => {
    const item = categories.find(c => c.value === category);
    return item?.label || category;
  };

  const columns = [
    {
      title: '风险类别',
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
            {level}
          </Tag>
        );
      },
    },
    {
      title: '拒答内容',
      dataIndex: 'template_content',
      key: 'template_content',
      ellipsis: true,
      width: 400,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ResponseTemplate) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          onClick={() => handleEdit(record)}
        >
          编辑拒答内容
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3>拒答答案库</h3>
        <p style={{ color: '#666', marginBottom: 16 }}>
          当检测到风险内容时，如果知识库中没有找到合适的回答，系统将使用这里配置的拒答内容进行回复。
        </p>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={false}
      />

      <Modal
        title="编辑拒答内容"
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
          >
            <Select disabled>
              {categories.map(category => (
                <Option key={category.value} value={category.value}>
                  {category.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="template_content"
            label="拒答内容"
            rules={[{ required: true, message: '请输入拒答内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入当触发此风险类别时的拒答内容"
              showCount
              maxLength={500}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ResponseTemplateManagement;