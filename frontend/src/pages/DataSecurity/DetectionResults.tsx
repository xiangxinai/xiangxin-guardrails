import React, { useState, useEffect } from 'react';
import { Table, Card, Tag, Space, Button, Modal, Descriptions } from 'antd';
import { EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import { dataSecurityApi } from '../../services/api';

interface DetectionResult {
  id: string;
  request_id: string;
  original_text: string;
  anonymized_text: string;
  entity_count: number;
  categories_detected: string[];
  created_at: string;
}

const DetectionResults: React.FC = () => {
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedResult, setSelectedResult] = useState<any>(null);

  useEffect(() => {
    loadResults();
  }, [currentPage, pageSize]);

  const loadResults = async () => {
    setLoading(true);
    try {
      const offset = (currentPage - 1) * pageSize;
      const response = await dataSecurityApi.getDetectionResults(pageSize, offset);
      setResults(response.items || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('Failed to load detection results:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (requestId: string) => {
    try {
      const result = await dataSecurityApi.getDetectionResult(requestId);
      setSelectedResult(result);
      setDetailModalVisible(true);
    } catch (error) {
      console.error('Failed to load result detail:', error);
    }
  };

  const columns = [
    {
      title: '请求ID',
      dataIndex: 'request_id',
      key: 'request_id',
      width: 200,
      ellipsis: true,
    },
    {
      title: '原始文本',
      dataIndex: 'original_text',
      key: 'original_text',
      ellipsis: true,
    },
    {
      title: '实体数量',
      dataIndex: 'entity_count',
      key: 'entity_count',
      width: 100,
      render: (count: number) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: '检测类别',
      dataIndex: 'categories_detected',
      key: 'categories_detected',
      width: 200,
      render: (categories: string[]) => (
        <Space wrap>
          {categories.slice(0, 3).map((cat) => (
            <Tag key={cat} color="green">
              {cat}
            </Tag>
          ))}
          {categories.length > 3 && <Tag>+{categories.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: '检测时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: DetectionResult) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.request_id)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="检测结果历史"
        bordered={false}
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadResults}>
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={results}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 20);
            },
          }}
        />
      </Card>

      <Modal
        title="检测结果详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedResult && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Descriptions column={1} bordered>
              <Descriptions.Item label="请求ID">{selectedResult.request_id}</Descriptions.Item>
              <Descriptions.Item label="实体数量">
                <Tag color="blue">{selectedResult.entity_count}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="检测类别">
                <Space wrap>
                  {selectedResult.categories_detected.map((cat: string) => (
                    <Tag key={cat} color="green">
                      {cat}
                    </Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="检测时间">
                {new Date(selectedResult.created_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            <div>
              <div style={{ marginBottom: 8, fontWeight: 'bold' }}>原始文本：</div>
              <div
                style={{
                  padding: 12,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 4,
                  whiteSpace: 'pre-wrap',
                  maxHeight: 200,
                  overflow: 'auto',
                }}
              >
                {selectedResult.original_text}
              </div>
            </div>

            <div>
              <div style={{ marginBottom: 8, fontWeight: 'bold' }}>脱敏后文本：</div>
              <div
                style={{
                  padding: 12,
                  backgroundColor: '#e6f7ff',
                  borderRadius: 4,
                  whiteSpace: 'pre-wrap',
                  maxHeight: 200,
                  overflow: 'auto',
                }}
              >
                {selectedResult.anonymized_text}
              </div>
            </div>

            {selectedResult.entities && selectedResult.entities.length > 0 && (
              <div>
                <div style={{ marginBottom: 8, fontWeight: 'bold' }}>检测到的实体：</div>
                <Table
                  columns={[
                    {
                      title: '实体类型',
                      dataIndex: 'entity_type',
                      key: 'entity_type',
                      render: (type: string) => <Tag color="blue">{type}</Tag>,
                    },
                    {
                      title: '识别文本',
                      key: 'text',
                      render: (_: any, record: any) =>
                        selectedResult.original_text.substring(record.start, record.end),
                    },
                    {
                      title: '位置',
                      key: 'position',
                      render: (_: any, record: any) => `${record.start} - ${record.end}`,
                    },
                    {
                      title: '置信度',
                      dataIndex: 'score',
                      key: 'score',
                      render: (score: number) => {
                        const percentage = (score * 100).toFixed(1);
                        return (
                          <Tag color={score > 0.8 ? 'green' : score > 0.5 ? 'orange' : 'red'}>
                            {percentage}%
                          </Tag>
                        );
                      },
                    },
                  ]}
                  dataSource={selectedResult.entities}
                  rowKey={(record, index) => `${record.entity_type}-${index}`}
                  pagination={false}
                  size="small"
                />
              </div>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default DetectionResults;
