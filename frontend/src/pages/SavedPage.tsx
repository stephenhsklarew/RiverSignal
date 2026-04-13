import { useSaved, type SavedItem } from '../components/SavedContext'

const TYPE_LABELS: Record<SavedItem['type'], string> = {
  reach: 'Saved Reaches',
  species: 'Saved Species',
  fly: 'Saved Flies',
  recreation: 'Saved Adventures',
  restoration: 'Saved Projects',
}

const TYPE_ORDER: SavedItem['type'][] = ['reach', 'species', 'fly', 'recreation', 'restoration']

export default function SavedPage() {
  const { listSaved, unsave } = useSaved()
  const all = listSaved()

  return (
    <div style={{ padding: '24px 16px 72px', maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ fontFamily: 'Fraunces, serif', fontSize: 24, marginBottom: 8 }}>Saved</h1>

      {all.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 32 }}>
          Nothing saved yet — tap the heart icon on any card to save it here.
        </p>
      ) : (
        TYPE_ORDER.map(type => {
          const items = all.filter(i => i.type === type)
          if (items.length === 0) return null
          return (
            <section key={type} style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                {TYPE_LABELS[type]}
              </h2>
              {items.map(item => (
                <div key={`${item.type}-${item.id}`} style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '10px 12px', background: 'var(--surface, #fff)',
                  borderRadius: 8, border: '1px solid var(--border)',
                  marginBottom: 6,
                }}>
                  {item.thumbnail && (
                    <img src={item.thumbnail} alt="" style={{ width: 40, height: 40, borderRadius: 6, objectFit: 'cover' }} />
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.label}
                    </div>
                    {item.sublabel && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.sublabel}</div>
                    )}
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {item.watershed} · saved {new Date(item.savedAt).toLocaleDateString()}
                    </div>
                  </div>
                  <button
                    onClick={() => unsave(item.type, item.id)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text-muted)', fontSize: 16, padding: 8,
                      minWidth: 36, minHeight: 36,
                    }}
                    aria-label={`Remove ${item.label} from saved`}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </section>
          )
        })
      )}
    </div>
  )
}
