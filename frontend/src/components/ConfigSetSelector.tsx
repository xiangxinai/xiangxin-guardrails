import React, { useState, useEffect } from 'react';
import { Select, message, Space, Button, Modal, Form, Input } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

const { Option } = Select;
const { TextArea } = Input;

interface ConfigSet {
  id: number;
  name: string;
  description?: string;
  is_default: boolean;
  tenant_id: string;
}

interface ConfigSetSelectorProps {
  value?: number;
  onChange: (configSetId: number) => void;
  allowCreate?: boolean;
  placeholder?: string;
  style?: React.CSSProperties;
}

/**
 * ConfigSetSelector - Reusable dropdown component for selecting config sets
 *
 * Features:
 * - Loads and displays all available config sets for the tenant
 * - Shows default config set with a badge
 * - Optional: Allows creating new config sets inline
 * - Automatically refreshes after creation
 *
 * Usage:
 * ```tsx
 * <ConfigSetSelector
 *   value={selectedConfigSet}
 *   onChange={setSelectedConfigSet}
 *   allowCreate={true}
 * />
 * ```
 */
const ConfigSetSelector: React.FC<ConfigSetSelectorProps> = ({
  value,
  onChange,
  allowCreate = false,
  placeholder,
  style,
}) => {
  const { t } = useTranslation();
  const [configSets, setConfigSets] = useState<ConfigSet[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createForm] = Form.useForm();
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadConfigSets();
  }, []);

  const loadConfigSets = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/config/risk-configs');
      const configs = response.data || [];
      setConfigSets(configs);

      // Auto-select default if no value and configs exist
      if (!value && configs.length > 0) {
        const defaultConfig = configs.find((c: ConfigSet) => c.is_default);
        if (defaultConfig) {
          onChange(defaultConfig.id);
        }
      }
    } catch (error: any) {
      message.error(t('configSet.loadError') || 'Failed to load config sets');
      console.error('Load config sets error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      setCreating(true);

      await api.post('/api/v1/config/risk-configs', {
        name: values.name,
        description: values.description,
        is_default: false,
      });

      message.success(t('configSet.createSuccess') || 'Config set created successfully');
      createForm.resetFields();
      setCreateModalVisible(false);

      // Reload and select new config
      await loadConfigSets();
    } catch (error: any) {
      if (error.errorFields) {
        // Form validation error - do nothing, form will show errors
        return;
      }
      message.error(t('configSet.createError') || 'Failed to create config set');
      console.error('Create config set error:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleCancel = () => {
    createForm.resetFields();
    setCreateModalVisible(false);
  };

  return (
    <>
      <Space.Compact style={{ width: '100%', ...style }}>
        <Select
          value={value}
          onChange={onChange}
          loading={loading}
          placeholder={placeholder || t('configSet.selectPlaceholder') || 'Select a config set'}
          style={{ flex: 1 }}
          showSearch
          optionFilterProp="children"
          filterOption={(input, option) =>
            (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
          }
        >
          {configSets.map((config) => (
            <Option key={config.id} value={config.id}>
              {config.name}
              {config.is_default && ` (${t('protectionTemplate.default') || 'Default'})`}
            </Option>
          ))}
        </Select>

        {allowCreate && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            {t('common.create')}
          </Button>
        )}
      </Space.Compact>

      <Modal
        title={t('configSet.createNew') || 'Create Config Set'}
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={handleCancel}
        confirmLoading={creating}
        okText={t('common.create')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={createForm}
          layout="vertical"
          name="create_config_set"
        >
          <Form.Item
            name="name"
            label={t('common.name')}
            rules={[
              { required: true, message: t('common.required') || 'This field is required' },
              { max: 100, message: t('common.maxLength', { max: 100 }) || 'Max length is 100' },
            ]}
          >
            <Input placeholder={t('configSet.namePlaceholder') || 'Enter config set name'} />
          </Form.Item>

          <Form.Item
            name="description"
            label={t('common.description')}
            rules={[
              { max: 500, message: t('common.maxLength', { max: 500 }) || 'Max length is 500' },
            ]}
          >
            <TextArea
              rows={3}
              placeholder={t('configSet.descriptionPlaceholder') || 'Enter description (optional)'}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ConfigSetSelector;
