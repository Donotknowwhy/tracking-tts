/** Job còn chạy / chờ (cần làm mới danh sách thường xuyên). Khớp terminal: completed | failed | cancelled. */
export function isJobStillActive(status: string): boolean {
  return !['completed', 'failed', 'cancelled'].includes(status)
}

/** Hiển thị trạng thái job (API vẫn trả tiếng Anh nội bộ). */
export function trangThaiJob(status: string): string {
  const map: Record<string, string> = {
    queued: 'Đang xếp hàng',
    running_t1: 'Đang chạy snapshot 1',
    running_t2: 'Đang chạy snapshot 2',
    waiting_t2: 'Chờ snapshot 2',
    analyzing: 'Đang phân tích',
    completed: 'Hoàn tất',
    failed: 'Lỗi',
    cancelled: 'Đã hủy',
  }
  return map[status] ?? status
}
