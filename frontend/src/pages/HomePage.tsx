import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Progress,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Link } from 'react-router-dom'
import {
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  PlayCircleOutlined,
  RedoOutlined,
  StopOutlined,
} from '@ant-design/icons'
import {
  fetchJobs,
  fetchSadcaptchaCredits,
  streamJobs,
  createJob,
  cancelJob,
  restartJob,
  type JobSummary,
  type SadcaptchaCredits,
} from '../api'
import { trangThaiJob } from '../statusLabels'
import { parseUrlsDedupe } from '../parseUrls'

const { Title, Paragraph } = Typography

function ProgressCell({ row }: { row: JobSummary }) {
  const p = row.progress
  const total = row.total_urls ?? 0
  if (!p || p.mode === 'none') {
    if (total > 0) {
      return (
        <Typography.Text type="secondary">
          {row.processed_urls ?? 0} / {total} URL
        </Typography.Text>
      )
    }
    return '—'
  }
  if (p.mode === 'urls' && total > 0) {
    return (
      <Progress
        percent={p.percent}
        size="small"
        status="active"
        style={{ width: '100%' }}
        format={() => `${p.processed} / ${p.total}`}
      />
    )
  }
  if (p.mode === 'waiting') {
    return (
      <span>
        Chờ snapshot 2
        {row.remain_text && row.remain_text !== '-' ? (
          <Typography.Text type="secondary" style={{ marginLeft: 6 }}>
            ({row.remain_text})
          </Typography.Text>
        ) : null}
      </span>
    )
  }
  if (p.mode === 'analyzing') {
    return <Typography.Text type="secondary">Phân tích…</Typography.Text>
  }
  if (total > 0) {
    return (
      <Typography.Text type="secondary">
        {row.processed_urls ?? 0} / {total} URL
      </Typography.Text>
    )
  }
  return '—'
}

function statusColor(status: string): string {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'cancelled') return 'default'
  if (status.startsWith('running')) return 'processing'
  if (status === 'waiting_t2') return 'warning'
  if (status === 'analyzing') return 'cyan'
  return 'blue'
}

export default function HomePage() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [jobs, setJobs] = useState<JobSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [captchaCredits, setCaptchaCredits] = useState<SadcaptchaCredits | null>(null)
  const [captchaLoading, setCaptchaLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      setJobs(await fetchJobs())
    } catch {
      message.error('Không tải được danh sách job')
    } finally {
      setLoading(false)
    }
  }

  const loadCaptchaCredits = async () => {
    setCaptchaLoading(true)
    try {
      setCaptchaCredits(await fetchSadcaptchaCredits())
    } catch {
      setCaptchaCredits({
        enabled: true,
        credits: null,
        ok: false,
        message: 'Không kiểm tra được credits SadCaptcha',
      })
    } finally {
      setCaptchaLoading(false)
    }
  }

  useEffect(() => {
    load()
    loadCaptchaCredits()
    const cleanup = streamJobs((jobs) => {
      setJobs(jobs)
      setLoading(false)
    })
    return cleanup
  }, [])

  const submitJob = async (
    urlsClean: string,
    values: {
      job_name?: string
      interval_hours: number
      seo_keywords?: string
      win_keywords?: string
    },
  ) => {
    setSubmitting(true)
    try {
      const { job_id } = await createJob({
        urls: urlsClean,
        interval_hours: values.interval_hours ?? 3,
        job_name: values.job_name?.trim() ?? '',
        seo_keywords: values.seo_keywords ?? '',
        win_keywords: values.win_keywords ?? '',
      })
      message.success('Đã tạo job')
      navigate(`/jobs/${job_id}`)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'Lỗi tạo job')
    } finally {
      setSubmitting(false)
    }
  }

  const onFinish = async (values: {
    job_name?: string
    urls: string
    interval_hours: number
    seo_keywords?: string
    win_keywords?: string
  }) => {
    const {
      urls: urlsClean,
      duplicateCount,
      removedDuplicateLines,
    } = parseUrlsDedupe(values.urls)
    if (!urlsClean.trim()) {
      message.error('Nhập ít nhất một URL hợp lệ')
      return
    }

    if (duplicateCount > 0) {
      Modal.confirm({
        title: `Đã loại bỏ ${duplicateCount} dòng trùng lặp`,
        icon: <InfoCircleOutlined />,
        width: 640,
        content: (
          <div>
            <Paragraph type="secondary" style={{ marginBottom: 12 }}>
              Các link sau trùng với một dòng đã xuất hiện phía trên (chỉ giữ bản
              đầu tiên). Kiểm tra danh sách rồi bấm Tiếp tục để tạo job — ô nhập
              sẽ được cập nhật theo danh sách đã gộp.
            </Paragraph>
            <List
              size="small"
              bordered
              dataSource={removedDuplicateLines}
              style={{ maxHeight: 280, overflow: 'auto' }}
              renderItem={(item) => (
                <List.Item style={{ wordBreak: 'break-all' }}>{item}</List.Item>
              )}
            />
          </div>
        ),
        okText: 'Tiếp tục tạo job',
        cancelText: 'Đóng',
        onOk: async () => {
          form.setFieldsValue({ urls: urlsClean })
          await submitJob(urlsClean, values)
        },
      })
      return
    }

    await submitJob(urlsClean, values)
  }

  const onCancelRow = async (id: string) => {
    try {
      await cancelJob(id)
      message.success('Đã gửi yêu cầu hủy')
      load()
    } catch {
      message.error('Hủy thất bại')
    }
  }

  const confirmCancelRow = (id: string) => {
    Modal.confirm({
      title: 'Xác nhận hủy job',
      icon: <ExclamationCircleOutlined />,
      content:
        'Bạn có chắc muốn hủy job này? Tiến trình sẽ dừng ở bước an toàn tiếp theo (không dừng ngay giữa một URL đang tải).',
      okText: 'Hủy job',
      okType: 'danger',
      cancelText: 'Đóng',
      onOk: () => onCancelRow(id),
    })
  }

  const onRestartRow = async (id: string) => {
    try {
      await restartJob(id)
      message.success('Đã chạy lại job')
      navigate(`/jobs/${id}`)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'Chạy lại thất bại')
    }
  }

  const columns: ColumnsType<JobSummary> = [
    {
      title: 'Mã job',
      dataIndex: 'job_short',
      width: 100,
      render: (_, row) => (
        <Link to={`/jobs/${row.job_id}`}>{row.job_short}</Link>
      ),
    },
    {
      title: 'Tên job',
      dataIndex: 'job_name',
      width: 140,
      ellipsis: true,
      render: (v) => v ?? '—',
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      width: 160,
      render: (s: string) => (
        <Tag color={statusColor(s)} style={{ margin: 0, whiteSpace: 'normal' }}>
          {trangThaiJob(s)}
        </Tag>
      ),
    },
    {
      title: 'Tiến độ',
      key: 'progress_col',
      width: 200,
      render: (_, row) => (
        <div style={{ minWidth: 160 }}>
          <ProgressCell row={row} />
        </div>
      ),
    },
    { title: 'Tạo lúc', dataIndex: 'created_at', width: 160 },
    {
      title: 'Thao tác',
      key: 'act',
      width: 200,
      render: (_, row) => {
        if (!row.can_cancel && !row.can_restart) return '—'
        return (
          <Space size="small" wrap>
            {row.can_cancel && (
              <Button
                size="small"
                danger
                icon={<StopOutlined />}
                onClick={() => confirmCancelRow(row.job_id)}
              >
                Hủy
              </Button>
            )}
            {row.can_restart && (
              <Button
                size="small"
                type="primary"
                icon={<RedoOutlined />}
                onClick={() => onRestartRow(row.job_id)}
              >
                Chạy lại
              </Button>
            )}
          </Space>
        )
      },
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={2} style={{ marginBottom: 4 }}>
          Theo dõi TikTok Shop
        </Title>
        <Paragraph type="secondary">
          Tạo job, theo dõi tiến độ và tải file kết quả. Thời gian hiển thị theo giờ Việt Nam
          (UTC+7).
        </Paragraph>
      </div>

      <Card
        title="SadCaptcha Credits"
        extra={
          <Button size="small" onClick={loadCaptchaCredits} loading={captchaLoading}>
            Refresh
          </Button>
        }
      >
        {captchaCredits ? (
          <Space direction="vertical" size={4}>
            <div>
              Trạng thái:{' '}
              <Tag color={captchaCredits.ok ? 'success' : 'error'}>
                {captchaCredits.ok ? 'OK' : 'Cần kiểm tra'}
              </Tag>
            </div>
            <Typography.Text>
              Credits còn lại:{' '}
              {captchaCredits.credits === null ? 'N/A' : captchaCredits.credits}
            </Typography.Text>
            <Typography.Text type={captchaCredits.ok ? 'secondary' : 'danger'}>
              {captchaCredits.message}
            </Typography.Text>
          </Space>
        ) : (
          <Typography.Text type="secondary">Đang tải credits SadCaptcha…</Typography.Text>
        )}
      </Card>

      <Card title="Chạy tracking mới">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ interval_hours: 3 }}
        >
          <Form.Item label="Tên job (tùy chọn)" name="job_name">
            <Input
              placeholder="Ví dụ: Phụ kiện điện thoại T4"
              maxLength={120}
            />
          </Form.Item>
          <Form.Item
            label="Danh sách URL (mỗi dòng một link)"
            name="urls"
            rules={[{ required: true, message: 'Nhập ít nhất một URL' }]}
            extra="Các dòng trùng nhau (cùng một link) sẽ tự động gộp lại khi tạo job."
          >
            <Input.TextArea
              rows={8}
              placeholder="https://www.tiktok.com/..."
            />
          </Form.Item>
          <Form.Item
            label="Từ khóa tối ưu SEO (tùy chọn — để tách khỏi keyword niche)"
            name="seo_keywords"
            extra="Mỗi dòng hoặc phân tách bằng dấu phẩy/chấm phẩy. Ví dụ: wash, vintage, streetwear, cotton, anime. Các từ/cụm khớp sẽ vào cột «Keyword tối ưu SEO» trong sheet Keywords; phần còn lại vào «Keyword niche»."
          >
            <Input.TextArea
              rows={4}
              placeholder={'wash\nvintage\nstreetwear'}
            />
          </Form.Item>
          <Form.Item
            label="Từ khóa cần kiểm tra mức độ win (tùy chọn)"
            name="win_keywords"
            extra="Mỗi dòng hoặc phân tách bằng dấu phẩy/chấm phẩy. Ví dụ: wash, vintage."
          >
            <Input.TextArea
              rows={3}
              placeholder={'K1\nK2'}
            />
          </Form.Item>
          <Form.Item label="Khoảng cách giữa 2 snapshot (giờ)" name="interval_hours">
            <InputNumber min={0} step={0.25} style={{ width: 200 }} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={submitting}
              icon={<PlayCircleOutlined />}
            >
              Chạy tracking
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Job gần đây">
        <Table<JobSummary>
          rowKey="job_id"
          loading={loading}
          columns={columns}
          dataSource={jobs}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          size="middle"
        />
      </Card>
    </Space>
  )
}
