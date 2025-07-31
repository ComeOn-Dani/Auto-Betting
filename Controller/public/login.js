// redirect if already logged in
if (localStorage.getItem('accessToken')) {
  window.location.replace('index.html');
}

document.getElementById('login-btn').addEventListener('click', async () => {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const errorEl = document.getElementById('error');
  errorEl.textContent = '';
  if (!username || !password) {
    errorEl.textContent = 'Please enter username and password';
    return;
  }
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!data.success) {
      errorEl.textContent = data.message || 'Login failed';
      return;
    }
    localStorage.setItem('accessToken', data.token);
    // redirect to controller
    window.location.href = 'index.html';
  } catch (err) {
    errorEl.textContent = 'Network error';
  }
}); 