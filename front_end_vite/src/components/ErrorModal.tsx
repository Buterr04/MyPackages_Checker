type ErrorModalProps = {
  open: boolean;
  title?: string;
  message: string;
  detail?: string;
  onClose: () => void;
};

function ErrorModal({ open, title = "请求失败", message, detail, onClose }: ErrorModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="error-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="error-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="error-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="row">
          <h3 id="error-modal-title">{title}</h3>
          <span className="tag">error</span>
        </div>
        <p className="error-modal-message">{message}</p>
        {detail ? <pre className="error-modal-detail">{detail}</pre> : null}
        <div className="error-modal-actions">
          <button type="button" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

export default ErrorModal;
