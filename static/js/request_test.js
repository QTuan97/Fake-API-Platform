// static/js/request_test.js
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('run-test');
  if (!btn) return;

  btn.addEventListener('click', async (e) => {
    e.preventDefault();

    const resultDiv = document.getElementById('test-result');
    resultDiv.innerHTML = '<em>Testing...</em>';
    const start = performance.now();

    const method    = btn.dataset.method;          // "GET"
    const template  = btn.dataset.templatePath;    // "/users/:id"
    const userId    = btn.dataset.userId;          // e.g. "1"

    // Build the actual path by replacing :id
    const path = template.replace(':id', userId);

    const options = {
      method,
      headers: {},
      credentials: 'include',
      redirect: 'manual'
    };

    // Include JSON body if present (for POST/PUT/etc)
    const bodyInput = document.getElementById('test-body');
    if (bodyInput) {
      const raw = bodyInput.value.trim();
      if (raw) {
        options.headers['Content-Type'] = 'application/json';
        options.body = raw;
      }
    }

    try {
      const resp = await fetch(path, options);
      const duration = Math.round(performance.now() - start);

      let html = `
        <div><strong>Status:</strong> ${resp.status} ${resp.statusText}</div>
        <div><strong>Time:</strong> ${duration} ms</div>
        <div><strong>Headers:</strong>
          <pre>${
            Array.from(resp.headers.entries())
                 .map(([k,v]) => `${k}: ${v}`)
                 .join('\n')
          }</pre>
        </div>
      `;

      const ct = resp.headers.get('Content-Type') || '';
      if (ct.includes('application/json')) {
        const json = await resp.json();
        html += `<pre>${JSON.stringify(json, null, 2)}</pre>`;
      } else {
        const text = await resp.text();
        html += `<pre>${text}</pre>`;
      }

      resultDiv.innerHTML = html;
    } catch (err) {
      resultDiv.innerHTML = `<span style="color:red;">Error: ${err.message}</span>`;
    }
  });
});
