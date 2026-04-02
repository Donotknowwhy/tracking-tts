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
  StopOutlined,
} from '@ant-design/icons'
import {
  fetchJobs,
  streamJobs,
  createJob,
  cancelJob,
  type JobSummary,
} from '../api'
import { trangThaiJob } from '../statusLabels'
import { parseUrlsDedupe } from '../parseUrls'

const { Title, Paragraph } = Typography

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

  useEffect(() => {
    load()
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

  const columns: ColumnsType<JobSummary> = [
    {
      title: 'Mã job',
      dataIndex: 'job_short',
      render: (_, row) => (
        <Link to={`/jobs/${row.job_id}`}>{row.job_short}</Link>
      ),
    },
    { title: 'Tên job', dataIndex: 'job_name', render: (v) => v ?? '—' },
    { title: 'Phiên', dataIndex: 'session_id', render: (v) => v ?? '—' },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      render: (s: string) => (
        <Tag color={statusColor(s)}>{trangThaiJob(s)}</Tag>
      ),
    },
    { title: 'Tạo lúc', dataIndex: 'created_at' },
    {
      title: 'Thao tác',
      key: 'act',
      render: (_, row) =>
        row.can_cancel ? (
          <Button
            size="small"
            danger
            icon={<StopOutlined />}
            onClick={() => confirmCancelRow(row.job_id)}
          >
            Hủy
          </Button>
        ) : (
          '—'
        ),
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
          pagination={false}
          size="middle"
        />
      </Card>
    </Space>
  )
}
