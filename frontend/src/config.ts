/** API base URL — configured via VITE_API_BASE env var at build time.
 *  Development: http://localhost:8001/api/v1
 *  Production:  https://your-cloud-run-url.run.app/api/v1
 */
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api/v1'
