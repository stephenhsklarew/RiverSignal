import { useAuth } from './AuthContext'
import './LoginModal.css'

interface LoginModalProps {
  onClose: () => void
  dark?: boolean
  mode?: 'signup' | 'signin'  // Controls title text
}

export default function LoginModal({ onClose, dark }: LoginModalProps) {
  const { loginWithGoogle, loginWithApple } = useAuth()

  return (
    <div className={`login-overlay ${dark ? 'dark' : ''}`} onClick={onClose}>
      <div className="login-modal" onClick={e => e.stopPropagation()}>
        <button type="button" className="login-close" onClick={onClose}>✕</button>

        <div className="login-header">
          <h2>Sign in or sign up</h2>
          <p>Sign in to an existing account or create one to save observations, sync settings, and use RiverPath across devices.</p>
        </div>

        <div className="login-buttons">
          <button type="button" className="login-btn google" onClick={() => loginWithGoogle()}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
              <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.26c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
              <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
              <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>

          <button type="button" className="login-btn apple" onClick={() => loginWithApple()}>
            <svg width="18" height="18" viewBox="0 0 18 22" fill="currentColor">
              <path d="M14.94 0c.1.97-.28 1.95-.83 2.65-.6.73-1.5 1.27-2.42 1.2-.12-.95.36-1.96.89-2.58C13.16.55 14.13.08 14.94 0ZM17.69 7.55c-.12.07-2.21 1.28-2.19 3.81.03 3.02 2.65 4.03 2.68 4.04-.02.07-.42 1.44-1.38 2.85-.83 1.22-1.7 2.44-3.06 2.46-1.34.03-1.77-.79-3.3-.79-1.53 0-2.01.77-3.28.82-1.32.04-2.32-1.32-3.16-2.53C2.27 15.73 1.12 12.07 2.87 9.6c.87-1.23 2.42-2.01 4.1-2.03 1.29-.02 2.51.87 3.3.87.78 0 2.26-1.08 3.8-.92.65.03 2.47.26 3.64 1.97l-.02.06Z"/>
            </svg>
            Continue with Apple
          </button>
        </div>

        <div className="login-footer">
          <p>Your data stays on your device until you sign in. No account required to use the app.</p>
        </div>
      </div>
    </div>
  )
}

/** Nudge banner — shown after anonymous save/observation */
export function LoginNudge({ dark, onDismiss }: { dark?: boolean; onDismiss: () => void }) {
  const { loginWithGoogle } = useAuth()

  return (
    <div className={`login-nudge ${dark ? 'dark' : ''}`}>
      <span className="login-nudge-text">Sign up to sync your finds across devices</span>
      <button className="login-nudge-btn" onClick={loginWithGoogle}>Sign up</button>
      <button className="login-nudge-dismiss" onClick={onDismiss}>✕</button>
    </div>
  )
}
