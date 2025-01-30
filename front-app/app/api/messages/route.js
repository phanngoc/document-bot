export async function GET(request) {
  const response = await fetch('http://127.0.0.1:5002/api/messages');
  if (!response.ok) {
    return new Response(JSON.stringify({ error: 'Failed to fetch messages' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  const messages = await response.json();
  return new Response(JSON.stringify(messages), {
    headers: { 'Content-Type': 'application/json' },
  });
}
