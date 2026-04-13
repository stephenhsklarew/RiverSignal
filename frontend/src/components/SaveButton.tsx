import { useSaved, type SavedItem } from './SavedContext'

interface SaveButtonProps {
  item: Omit<SavedItem, 'savedAt'>
  size?: number
}

export default function SaveButton({ item, size = 20 }: SaveButtonProps) {
  const { save, unsave, isSaved } = useSaved()
  const saved = isSaved(item.type, item.id)

  const toggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (saved) unsave(item.type, item.id)
    else save(item)
  }

  return (
    <button
      onClick={toggle}
      aria-label={saved ? `Remove ${item.label} from saved` : `Save ${item.label}`}
      style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        fontSize: size,
        color: saved ? 'var(--alert, #c4432b)' : 'var(--text-muted, #9e9b96)',
        padding: 6,
        lineHeight: 1,
        transition: 'transform 0.15s, color 0.15s',
        transform: saved ? 'scale(1.15)' : 'scale(1)',
        minWidth: 36,
        minHeight: 36,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {saved ? '♥' : '♡'}
    </button>
  )
}
