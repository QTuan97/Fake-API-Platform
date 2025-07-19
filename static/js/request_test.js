document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('run-test');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const resultDiv = document.getElementById('test-result');
    resultDiv.innerHTML = '<em>Testing...</em>';
    const start = performance.now();

    const method = btn.dataset.method;
    const path   = btn.dataset.path;

    try {
      const resp = await fetch(path, { method });
      const duration = Math.round(performance.now() - start);

      const contentType = resp.headers.get('Content-Type') || '';
      let body;
      if (contentType.includes('application/json')) {
        body = JSON.stringify(await resp.json(), null, 2);
      } else {
        body = await resp.text();
      }

      resultDiv.innerHTML = `
        <div><strong>Status:</strong> ${resp.status}</div>
        <div><strong>Time:</strong> ${duration} ms</div>
        <pre>${body}</pre>
      `;
    } catch (err) {
      resultDiv.innerHTML = `<span style="color:red;">Error: ${err.message}</span>`;
    }
  });
});
