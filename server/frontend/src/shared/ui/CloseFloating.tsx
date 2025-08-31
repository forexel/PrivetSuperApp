import CloseIcon from '../../assets/icons/close.svg?react'

type Props = { onClick: () => void; ariaLabel?: string }

export function CloseFloating({ onClick, ariaLabel = 'Закрыть' }: Props) {
  return (
    <button className="close-floating" aria-label={ariaLabel} onClick={onClick}>
      <CloseIcon className="close-floating-icon" />
    </button>
  )
}