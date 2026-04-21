import { useState } from 'react'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import './LoginModal.css'

/** Check if this browser has ever logged in before */
function hasLoggedInBefore(): boolean {
  return localStorage.getItem('rs_has_account') === 'true'
}

function markHasAccount() {
  localStorage.setItem('rs_has_account', 'true')
}

export default function UserMenu({ dark }: { dark?: boolean }) {
  const { user, isLoggedIn, logout } = useAuth()
  const [showLogin, setShowLogin] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  // Mark that this browser has an account once logged in
  if (isLoggedIn) markHasAccount()

  if (!isLoggedIn) {
    const isReturning = hasLoggedInBefore()
    return (
      <>
        <button
          className="login-nudge-btn"
          style={{ fontSize: '0.72rem', padding: '5px 12px' }}
          onClick={() => setShowLogin(true)}
        >
          {isReturning ? 'Sign In' : 'Sign Up'}
        </button>
        {showLogin && (
          <LoginModal
            onClose={() => setShowLogin(false)}
            dark={dark}
            mode={isReturning ? 'signin' : 'signup'}
          />
        )}
      </>
    )
  }

  return (
    <div className="user-menu" onClick={() => setShowDropdown(!showDropdown)}>
      {user?.avatar ? (
        <img src={user.avatar} alt={user.name} className="user-avatar" />
      ) : (
        <div className="user-avatar" style={{
          background: dark ? '#3d3328' : '#e8e5de',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.7rem', fontWeight: 600,
          color: dark ? '#d4a96a' : '#1a6b4a',
        }}>
          {(user?.username || user?.name || 'U')[0].toUpperCase()}
        </div>
      )}

      {showDropdown && (
        <div className="user-dropdown" style={dark ? { background: '#2a2318', borderColor: '#3d3328' } : {}}>
          <div className="user-dropdown-item" style={{ cursor: 'default', fontWeight: 600 }}>
            {user?.username ? `@${user.username}` : user?.name}
          </div>
          <div className="user-dropdown-item" style={{ cursor: 'default', fontSize: '0.72rem', color: '#999' }}>
            {user?.email}
          </div>
          <button className="user-dropdown-item danger" onClick={(e) => { e.stopPropagation(); logout(); setShowDropdown(false) }}>
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
