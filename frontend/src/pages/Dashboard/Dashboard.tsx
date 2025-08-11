import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Spin, Alert } from 'antd';
import {
  SafetyOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  FileProtectOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { dashboardApi } from '../../services/api';
import type { DashboardStats } from '../../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await dashboardApi.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('获取统计数据失败');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskDistributionOption = () => {
    if (!stats) return {};

    return {
      title: {
        text: '风险等级分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          name: '风险等级',
          type: 'pie',
          radius: '50%',
          data: [
            { value: stats.risk_distribution['高风险'], name: '高风险', itemStyle: { color: '#ff4d4f' } },
            { value: stats.risk_distribution['中风险'], name: '中风险', itemStyle: { color: '#faad14' } },
            { value: stats.risk_distribution['低风险'], name: '低风险', itemStyle: { color: '#fadb14' } },
            { value: stats.risk_distribution['无风险'], name: '安全通过', itemStyle: { color: '#52c41a' } },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };
  };

  const getTrendOption = () => {
    if (!stats) return {};

    const dates = stats.daily_trends.map(item => item.date);
    const totalData = stats.daily_trends.map(item => item.total);
    const highRiskData = stats.daily_trends.map(item => item.high_risk);
    const mediumRiskData = stats.daily_trends.map(item => item.medium_risk);

    return {
      title: {
        text: '检测趋势（最近7天）',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        data: ['总检测数', '高风险', '中风险'],
        bottom: 0,
      },
      xAxis: {
        type: 'category',
        data: dates,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '总检测数',
          type: 'line',
          data: totalData,
          itemStyle: { color: '#1890ff' },
        },
        {
          name: '高风险',
          type: 'line',
          data: highRiskData,
          itemStyle: { color: '#ff4d4f' },
        },
        {
          name: '中风险',
          type: 'line',
          data: mediumRiskData,
          itemStyle: { color: '#faad14' },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="错误"
        description={error}
        type="error"
        showIcon
        action={
          <button onClick={fetchStats} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
            重试
          </button>
        }
      />
    );
  }

  if (!stats) return null;

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统总览</h2>
      
      {/* 总体统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总检测数"
              value={stats.total_requests}
              prefix={<FileProtectOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发现安全风险"
              value={stats.security_risks}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#fa8c16' }}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发现合规风险"
              value={stats.compliance_risks}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总风险检出"
              value={stats.high_risk_count + stats.medium_risk_count + stats.low_risk_count}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff7a45' }}
              suffix="次"
            />
          </Card>
        </Col>
      </Row>

      {/* 风险等级分布 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="高风险检出"
              value={stats.high_risk_count}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="中风险检出"
              value={stats.medium_risk_count}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="低风险检出"
              value={stats.low_risk_count}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#fadb14' }}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="安全通过"
              value={stats.safe_count}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix="次"
            />
          </Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card>
            <ReactECharts option={getRiskDistributionOption()} style={{ height: 400 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <ReactECharts option={getTrendOption()} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;