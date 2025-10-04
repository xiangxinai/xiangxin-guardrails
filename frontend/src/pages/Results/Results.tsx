import React, { useEffect, useState } from 'react';
import { Table, Card, Select, DatePicker, Space, Tag, Button, Drawer, Typography, Row, Col, Input, Spin, Image } from 'antd';
import { EyeOutlined, ReloadOutlined, SearchOutlined, FileImageOutlined, PictureOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { resultsApi } from '../../services/api';
import type { DetectionResult, PaginatedResponse } from '../../types';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Paragraph } = Typography;

const Results: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<DetectionResult> | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<DetectionResult | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filters, setFilters] = useState({
    risk_level: undefined as string | undefined,
    result_type: undefined as string | undefined,
    category: undefined as string | undefined,
    date_range: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
    content_search: undefined as string | undefined,
    request_id_search: undefined as string | undefined,
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
  });

  useEffect(() => {
    fetchResults();
  }, [pagination.current, pagination.pageSize, filters]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const params: any = {
        page: pagination.current,
        per_page: pagination.pageSize,
      };

      if (filters.risk_level) {
        params.risk_level = filters.risk_level;
      }
      if (filters.result_type) {
        params.result_type = filters.result_type;
      }
      if (filters.category) {
        params.category = filters.category;
      }
      if (filters.date_range) {
        params.start_date = filters.date_range[0].format('YYYY-MM-DD');
        params.end_date = filters.date_range[1].format('YYYY-MM-DD');
      }
      if (filters.content_search) {
        params.content_search = filters.content_search;
      }
      if (filters.request_id_search) {
        params.request_id_search = filters.request_id_search;
      }

      const result = await resultsApi.getResults(params);
      setData(result);
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (paginationParams: any) => {
    setPagination({
      current: paginationParams.current,
      pageSize: paginationParams.pageSize,
    });
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    setPagination(prev => ({ ...prev, current: 1 })); // 重置页码
  };

  const showDetail = async (record: DetectionResult) => {
    setDetailLoading(true);
    setDrawerVisible(true);
    try {
      // 调用详情API获取完整内容
      const fullRecord = await resultsApi.getResult(record.id);
      console.log('Full record from API:', fullRecord);
      console.log('has_image:', fullRecord.has_image);
      console.log('image_count:', fullRecord.image_count);
      console.log('image_paths:', fullRecord.image_paths);
      setSelectedResult(fullRecord);
    } catch (error) {
      console.error('Failed to fetch full record:', error);
      // 如果获取详情失败，仍然显示截断的内容
      setSelectedResult(record);
    } finally {
      setDetailLoading(false);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case '高风险': return 'red';
      case '中风险': return 'orange';
      case '低风险': return 'yellow';
      case '无风险': return 'green';
      default: return 'default';
    }
  };

  // Helper function to format risk display
  const formatRiskDisplay = (riskLevel: string, categories: string[]) => {
    if (riskLevel === '无风险') {
      return '无风险';
    }
    if (categories && categories.length > 0) {
      return `${riskLevel} ${categories[0]}`;
    }
    return riskLevel;
  };

  // Helper function to format request ID display - show latter half with ellipsis
  const formatRequestId = (requestId: string) => {
    if (requestId.length <= 20) {
      return requestId;
    }
    // Show last 18 characters with ellipsis at the beginning
    return '...' + requestId.slice(-18);
  };

  // 定义所有风险类别
  const getAllCategories = () => {
    return [
      '敏感政治话题',
      '损害国家形象',
      '暴力犯罪',
      '提示词攻击',
      '一般政治话题',
      '伤害未成年人',
      '违法犯罪',
      '色情',
      '歧视内容',
      '辱骂',
      '侵犯个人隐私',
      '商业违法违规'
    ];
  };

  const columns = [
    {
      title: '检测内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: {
        showTitle: false,
      },
      width: 250,
      render: (text: string, record: DetectionResult) => (
        <span
          style={{ cursor: 'pointer', color: '#1890ff' }}
          onClick={() => showDetail(record)}
        >
          {record.has_image && (
            <Tag color="blue" icon={<FileImageOutlined />} style={{ marginRight: 8 }}>
              {record.image_count}张图片
            </Tag>
          )}
          <span title={text}>{text}</span>
        </span>
      ),
    },
    {
      title: '请求ID',
      dataIndex: 'request_id',
      key: 'request_id',
      width: 140,
      render: (text: string) => (
        <span 
          title={text} 
          style={{ 
            cursor: 'pointer',
            fontSize: '12px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: 'block',
            maxWidth: '130px'
          }}
        >
          {formatRequestId(text)}
        </span>
      ),
    },
    {
      title: '提示词攻击',
      key: 'prompt_attack',
      width: 150,
      render: (_: any, record: DetectionResult) => {
        const riskLevel = record.security_risk_level || '无风险';
        const categories = record.security_categories || [];
        const displayText = formatRiskDisplay(riskLevel, categories);
        
        return (
          <Tag 
            color={getRiskLevelColor(riskLevel)} 
            style={{ fontSize: '12px' }}
            title={categories.join(', ')}
          >
            {displayText}
          </Tag>
        );
      },
    },
    {
      title: '内容合规',
      key: 'content_compliance',
      width: 150,
      render: (_: any, record: DetectionResult) => {
        const riskLevel = record.compliance_risk_level || '无风险';
        const categories = record.compliance_categories || [];
        const displayText = formatRiskDisplay(riskLevel, categories);

        return (
          <Tag
            color={getRiskLevelColor(riskLevel)}
            style={{ fontSize: '12px' }}
            title={categories.join(', ')}
          >
            {displayText}
          </Tag>
        );
      },
    },
    {
      title: '数据泄漏',
      key: 'data_leak',
      width: 150,
      render: (_: any, record: DetectionResult) => {
        const riskLevel = record.data_risk_level || '无风险';
        const categories = record.data_categories || [];
        const displayText = formatRiskDisplay(riskLevel, categories);

        return (
          <Tag
            color={getRiskLevelColor(riskLevel)}
            style={{ fontSize: '12px' }}
            title={categories.join(', ')}
          >
            {displayText}
          </Tag>
        );
      },
    },
    {
      title: '建议动作',
      dataIndex: 'suggest_action',
      key: 'suggest_action',
      width: 90,
      render: (action: string) => {
        const color = action === '通过' ? 'green' : action === '拒答' ? 'red' : 'orange';
        return <Tag color={color} style={{ fontSize: '12px' }}>{action}</Tag>;
      },
    },
    {
      title: '检测时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (time: string) => (
        <span style={{ fontSize: '12px' }} title={dayjs(time).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(time).format('MM-DD HH:mm')}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 70,
      fixed: 'right' as const,
      render: (_: any, record: DetectionResult) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          size="small"
          onClick={() => showDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>检测结果</h2>
      
      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          
          <Select
            placeholder="选择风险等级"
            allowClear
            size="middle"
            style={{ width: 120 }}
            value={filters.risk_level}
            onChange={(value) => handleFilterChange('risk_level', value)}
          >
            <Option value="高风险">高风险</Option>
            <Option value="中风险">中风险</Option>
            <Option value="低风险">低风险</Option>
            <Option value="无风险">无风险</Option>
          </Select>
          
          
          <Select
            placeholder="选择风险类别"
            allowClear
            size="middle"
            style={{ width: 150 }}
            value={filters.category}
            onChange={(value) => handleFilterChange('category', value)}
          >
            {getAllCategories().map(category => (
              <Option key={category} value={category}>{category}</Option>
            ))}
          </Select>
          
          <Input
            placeholder="搜索检测内容"
            allowClear
            size="middle"
            style={{ width: 200, height: 32 }}
            prefix={<SearchOutlined />}
            value={filters.content_search}
            onChange={(e) => handleFilterChange('content_search', e.target.value || undefined)}
          />
          
          <Input
            placeholder="搜索请求ID"
            allowClear
            size="middle"
            style={{ width: 200, height: 32 }}
            prefix={<SearchOutlined />}
            value={filters.request_id_search}
            onChange={(e) => handleFilterChange('request_id_search', e.target.value || undefined)}
          />
          
          <RangePicker
            placeholder={['开始日期', '结束日期']}
            value={filters.date_range}
            onChange={(dates) => handleFilterChange('date_range', dates)}
          />
          
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchResults}
          >
            刷新
          </Button>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={loading}
          size="small"
          tableLayout="fixed"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            size: 'small',
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Drawer
        title="检测结果详情"
        width={720}
        onClose={() => {
          setDrawerVisible(false);
          setSelectedResult(null);
        }}
        open={drawerVisible}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>加载详细内容中...</div>
          </div>
        ) : selectedResult && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>请求ID:</Text>
              </Col>
              <Col span={16}>
                <Text code>{selectedResult.request_id}</Text>
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>提示词攻击:</Text>
              </Col>
              <Col span={16}>
                <Tag color={getRiskLevelColor(selectedResult.security_risk_level || '无风险')}>
                  {formatRiskDisplay(selectedResult.security_risk_level || '无风险', selectedResult.security_categories || [])}
                </Tag>
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>内容合规:</Text>
              </Col>
              <Col span={16}>
                <Tag color={getRiskLevelColor(selectedResult.compliance_risk_level || '无风险')}>
                  {formatRiskDisplay(selectedResult.compliance_risk_level || '无风险', selectedResult.compliance_categories || [])}
                </Tag>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>数据泄漏:</Text>
              </Col>
              <Col span={16}>
                <Tag color={getRiskLevelColor(selectedResult.data_risk_level || '无风险')}>
                  {formatRiskDisplay(selectedResult.data_risk_level || '无风险', selectedResult.data_categories || [])}
                </Tag>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>建议动作:</Text>
              </Col>
              <Col span={16}>
                <Tag color={selectedResult.suggest_action === '通过' ? 'green' : selectedResult.suggest_action === '拒答' ? 'red' : 'orange'}>
                  {selectedResult.suggest_action}
                </Tag>
              </Col>
            </Row>
            
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Text strong>检测时间:</Text>
              </Col>
              <Col span={16}>
                <Text>{dayjs(selectedResult.created_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
              </Col>
            </Row>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>检测内容:</Text>
              <div
                style={{
                  marginTop: 8,
                  padding: 12,
                  background: '#f5f5f5',
                  borderRadius: 4,
                }}
              >
                {/* 显示文本内容 */}
                {selectedResult.content && (
                  <Paragraph style={{ marginBottom: selectedResult.has_image ? 12 : 0 }}>
                    {selectedResult.content}
                  </Paragraph>
                )}

                {/* 如果有图片，在内容中显示缩略图 */}
                {selectedResult.has_image && selectedResult.image_urls && selectedResult.image_urls.length > 0 ? (
                  <div style={{ marginTop: 12 }}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      检测图片 ({selectedResult.image_count}张):
                    </Text>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                      {selectedResult.image_urls.map((imageUrl, index) => {
                        return (
                          <div
                            key={index}
                            style={{
                              border: '1px solid #d9d9d9',
                              borderRadius: 4,
                              padding: 4,
                              background: '#fafafa'
                            }}
                          >
                            <Image
                              src={imageUrl}
                              alt={`检测图片 ${index + 1}`}
                              style={{
                                width: 150,
                                height: 150,
                                objectFit: 'cover',
                                borderRadius: 4
                              }}
                            />
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                display: 'block',
                                marginTop: 4,
                                textAlign: 'center'
                              }}
                            >
                              图片 {index + 1}
                            </Text>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                内容长度: {selectedResult.content.length} 字符
                {selectedResult.has_image && ` | 包含 ${selectedResult.image_count} 张图片`}
              </Text>
            </div>
            
            {selectedResult.suggest_answer && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>建议回答:</Text>
                <Paragraph
                  style={{
                    marginTop: 8,
                    padding: 12,
                    background: '#f0f8ff',
                    borderRadius: 4,
                  }}
                >
                  {selectedResult.suggest_answer}
                </Paragraph>
              </div>
            )}
            
            {((selectedResult.security_categories && selectedResult.security_categories.length > 0) ||
              (selectedResult.compliance_categories && selectedResult.compliance_categories.length > 0) ||
              (selectedResult.data_categories && selectedResult.data_categories.length > 0)) && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>风险详情:</Text>
                <div style={{ marginTop: 8 }}>
                  {selectedResult.security_categories && selectedResult.security_categories.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong style={{ fontSize: '12px' }}>提示词攻击: </Text>
                      {selectedResult.security_categories.map((category, index) => (
                        <Tag key={`security-${index}`} color="red" style={{ marginBottom: 4 }}>
                          {category}
                        </Tag>
                      ))}
                    </div>
                  )}
                  {selectedResult.compliance_categories && selectedResult.compliance_categories.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <Text strong style={{ fontSize: '12px' }}>内容合规: </Text>
                      {selectedResult.compliance_categories.map((category, index) => (
                        <Tag key={`compliance-${index}`} color="orange" style={{ marginBottom: 4 }}>
                          {category}
                        </Tag>
                      ))}
                    </div>
                  )}
                  {selectedResult.data_categories && selectedResult.data_categories.length > 0 && (
                    <div>
                      <Text strong style={{ fontSize: '12px' }}>数据泄漏: </Text>
                      {selectedResult.data_categories.map((category, index) => (
                        <Tag key={`data-${index}`} color="magenta" style={{ marginBottom: 4 }}>
                          {category}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {selectedResult.ip_address && (
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={8}>
                  <Text strong>来源IP:</Text>
                </Col>
                <Col span={16}>
                  <Text code>{selectedResult.ip_address}</Text>
                </Col>
              </Row>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Results;