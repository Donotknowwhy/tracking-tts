import { useEffect, useState, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Descriptions,
  List,
  Modal,
  Progress,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import { ArrowLeftOutlined, ExclamationCircleOutlined, StopOutlined } from '@ant-design/icons'
import { fetchJob, streamJob, cancelJob, fileUrl, type JobDetail } from '../api'
import { trangThaiJob } from '../statusLabels'

const { Title } = Typography

function statusColor(status: string): string {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'cancelled') return 'default'
  if (status.startsWith('running')) return 'processing'
  if (status === 'waiting_t2') return 'warning'
  if (status === 'analyzing') return 'cyan'
  return 'blue'
}

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [job, setJob] = useState<JobDetail | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!jobId) return
    try {
      const d = await fetchJob(jobId)
      setJob(d)
    } catch {
      setJob(null)
      message.error('Không tìm thấy job')
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  useEffect(() => {
    if (!jobId) return
    const cleanup = streamJob(jobId, (data) => {
      setJob(data)
      setLoading(false)
    })
    return cleanup
  }, [jobId])

  const doCancel = async () => {
    if (!jobId) return
    try {
      await cancelJob(jobId)
      message.success('Đã gửi yêu cầu hủy')
      load()
    } catch {
      message.error('Hủy thất bại')
    }
  }

  const confirmCancel = () => {
    Modal.confirm({
      title: 'Xác nhận hủy job',
      icon: <ExclamationCircleOutlined />,
      content:
        'Bạn có chắc muốn hủy job này? Tiến trình sẽ dừng ở bước an toàn tiếp theo (không dừng ngay giữa một URL đang tải).',
      okText: 'Hủy job',
      okType: 'danger',
      cancelText: 'Đóng',
      onOk: () => doCancel(),
    })
  }

  if (!jobId) return null

  if (!job && !loading) {
    return (
      <Card>
        <Title level={4}>Không tìm thấy job</Title>
        <Link to="/">Về trang chủ</Link>
      </Card>
    )
  }

  const p = job?.progress
  const isSnapshotRunning =
    job?.status === 'running_t1' || job?.status === 'running_t2'

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Link to="/">
        <Button type="link" icon={<ArrowLeftOutlined />}>
          Quay lại
        </Button>
      </Link>

      <div>
        <Title level={2} style={{ marginTop: 0, marginBottom: 4 }}>
          Chi tiết job {jobId.slice(0, 8)}
          {job?.job_name ? ` — ${job.job_name}` : ''}
        </Title>
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          Thời gian theo giờ Việt Nam (UTC+7).
        </Typography.Text>
      </div>

      <Card loading={loading}>
        {job && (
          <>
            <Space style={{ marginBottom: 16 }} wrap>
              {job.can_cancel && (
                <Button danger icon={<StopOutlined />} onClick={confirmCancel}>
                  Hủy job
                </Button>
              )}
              <Tag color={statusColor(job.status)}>
                {trangThaiJob(job.status)}
              </Tag>
            </Space>

            {isSnapshotRunning && (
              <div
                style={{
                  marginBottom: 16,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <Spin size="small" />
                <Typography.Text type="secondary">
                  Đang chạy snapshot… Thu thập dữ liệu từng URL cho đến khi xong.
                </Typography.Text>
              </div>
            )}

            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Tên job">
                {job.job_name ?? '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Thông báo">{job.message}</Descriptions.Item>
              <Descriptions.Item label="Mã phiên (session)">
                {job.session_id ?? '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Tổng số URL">
                {job.total_urls ?? '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Còn lại (chờ snapshot 2)">
                {job.remain_text}
              </Descriptions.Item>
              <Descriptions.Item label="Tạo lúc">{job.created_at}</Descriptions.Item>
              <Descriptions.Item label="Hoàn tất lúc">{job.completed_at}</Descriptions.Item>
            </Descriptions>

            {p?.mode === 'urls' && (
              <div style={{ marginTop: 24 }}>
                <Typography.Text strong>Tiến độ URL</Typography.Text>
                <Progress
                  percent={p.percent}
                  status="active"
                  format={() => `${p.processed} / ${p.total}`}
                />
              </div>
            )}
            {p?.mode === 'waiting' && (
              <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
                Đã xong snapshot 1. Đang chờ tới snapshot 2…
              </Typography.Paragraph>
            )}
            {p?.mode === 'analyzing' && (
              <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
                Đang phân tích và xuất báo cáo…
              </Typography.Paragraph>
            )}
          </>
        )}
      </Card>

      <Card title="File kết quả">
        {job?.outputs?.length ? (
          <List
            dataSource={job.outputs}
            renderItem={(name) => (
              <List.Item>
                <a href={fileUrl(name)} target="_blank" rel="noreferrer">
                  {name}
                </a>
              </List.Item>
            )}
          />
        ) : (
          <Typography.Text type="secondary">
            Chưa có file output.
          </Typography.Text>
        )}
      </Card>
    </Space>
  )
}
