// Configuration for different environments
const config = {
  // Detect if we're running on Vercel
  isVercel: window.location.hostname.includes('vercel.app') || window.location.hostname.includes('vercel.com'),
  
  // WebSocket base URL
  get wsBase() {
    if (this.isVercel) {
      // Use secure WebSocket for Vercel deployment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}/api/ws`;
    } else {
      // Local development
      return 'ws://localhost:8080';
    }
  },
  
  // API base URL
  get apiBase() {
    if (this.isVercel) {
      return `${window.location.protocol}//${window.location.host}`;
    } else {
      return 'http://localhost:3000';
    }
  }
};

// Export for use in other scripts
window.appConfig = config;
