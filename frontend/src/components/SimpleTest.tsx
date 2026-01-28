/**
 * Simple Test Component - Verify API connection
 */

import { useState, useEffect } from 'react';

export function SimpleTest() {
  const [status, setStatus] = useState('Testing...');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/health')
      .then(res => res.json())
      .then(data => {
        setStatus('Connected!');
        setData(data);
      })
      .catch(err => {
        setStatus('Error: ' + err.message);
      });
  }, []);

  return (
    <div style={{ padding: '2rem', background: '#1a1a1a', color: '#fff', minHeight: '100vh' }}>
      <h1>Simple API Test</h1>
      <p>Status: {status}</p>
      {data && (
        <pre style={{ background: '#0a0a0a', padding: '1rem', borderRadius: '4px' }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
