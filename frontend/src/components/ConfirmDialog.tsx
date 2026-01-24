import React from 'react'
import './ConfirmDialog.css'

export interface ConfirmDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean
  /** Dialog title */
  title: string
  /** Dialog message/body */
  message: string
  /** Text for the confirm button */
  confirmText?: string
  /** Text for the cancel button */
  cancelText?: string
  /** Callback when user confirms */
  onConfirm: () => void
  /** Callback when user cancels */
  onCancel: () => void
  /** Variant for different actions */
  variant?: 'danger' | 'warning' | 'info'
}

/**
 * ConfirmDialog Component
 * 
 * A reusable, accessible confirmation dialog that replaces window.confirm().
 * 
 * Features:
 * - Accessible with ARIA labels and keyboard navigation
 * - Multiple variants (danger, warning, info)
 * - Customizable button text
 * - Focus management and ESC key support
 * - Modal backdrop to prevent interaction with background
 * 
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false)
 * 
 * <ConfirmDialog
 *   isOpen={isOpen}
 *   title="Delete Item"
 *   message="Are you sure you want to delete this item? This action cannot be undone."
 *   variant="danger"
 *   onConfirm={() => {
 *     deleteItem()
 *     setIsOpen(false)
 *   }}
 *   onCancel={() => setIsOpen(false)}
 * />
 * ```
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'info',
}) => {
  const dialogRef = React.useRef<HTMLDivElement>(null)

  // Handle ESC key
  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onCancel()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Focus trap
      dialogRef.current?.focus()
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onCancel])

  // Handle backdrop click
  const handleBackdropClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onCancel()
    }
  }

  if (!isOpen) {
    return null
  }

  return (
    <div
      className="confirm-dialog-backdrop"
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={dialogRef}
        className={`confirm-dialog confirm-dialog-${variant}`}
        role="alertdialog"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        aria-modal="true"
        tabIndex={-1}
      >
        <div className="confirm-dialog-header">
          <h2 id="confirm-dialog-title" className="confirm-dialog-title">
            {title}
          </h2>
        </div>

        <div className="confirm-dialog-body">
          <p id="confirm-dialog-message" className="confirm-dialog-message">
            {message}
          </p>
        </div>

        <div className="confirm-dialog-footer">
          <button
            onClick={onCancel}
            className="btn btn-secondary"
            type="button"
            autoFocus
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`btn btn-${variant}`}
            type="button"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog

/**
 * Hook for using ConfirmDialog in a component
 * 
 * @example
 * ```tsx
 * const { isOpen, show, hide, ConfirmDialog: Dialog } = useConfirmDialog({
 *   title: 'Delete Item',
 *   message: 'Are you sure?',
 *   onConfirm: () => deleteItem(),
 * })
 * 
 * return (
 *   <>
 *     <button onClick={show}>Delete</button>
 *     <Dialog />
 *   </>
 * )
 * ```
 */
export function useConfirmDialog(props: Omit<ConfirmDialogProps, 'isOpen' | 'onCancel'>) {
  const [isOpen, setIsOpen] = React.useState(false)

  const show = React.useCallback(() => setIsOpen(true), [])
  const hide = React.useCallback(() => setIsOpen(false), [])

  const Dialog = React.useCallback(
    () => (
      <ConfirmDialog
        {...props}
        isOpen={isOpen}
        onCancel={hide}
        onConfirm={() => {
          props.onConfirm()
          hide()
        }}
      />
    ),
    [props, isOpen, hide]
  )

  return { isOpen, show, hide, ConfirmDialog: Dialog }
}
