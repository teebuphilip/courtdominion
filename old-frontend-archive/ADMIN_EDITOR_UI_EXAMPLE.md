# Example Admin Editor UI (Next.js)

'use client';
import { useState } from 'react';

export default function AdminEditor() {
  const [jsonText, setJsonText] = useState("");

  async function save() {
    await fetch('/api/marketing', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + process.env.NEXT_PUBLIC_ADMIN_TOKEN,
        'Content-Type': 'application/json'
      },
      body: jsonText
    });
    alert("Updated!");
  }

  return (
    <div>
      <h1>Marketing Content Editor</h1>
      <textarea value={jsonText} onChange={e=>setJsonText(e.target.value)} />
      <button onClick={save}>Save</button>
    </div>
  );
}
