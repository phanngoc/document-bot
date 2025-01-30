export async function GET(request) {
  const response = await fetch('http://127.0.0.1:5002/api/assistants');
  if (!response.ok) {
    return new Response(JSON.stringify({ error: 'Failed to fetch assistants' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  const assistants = await response.json();
  return new Response(JSON.stringify(assistants), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST(request) {
  const data = await request.json();
  const response = await fetch('http://127.0.0.1:5002/api/assistants', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const newAssistant = await response.json();
  return new Response(JSON.stringify(newAssistant), {
    headers: { 'Content-Type': 'application/json' },
    status: 201,
  });
}
