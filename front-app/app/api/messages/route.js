export async function GET(request) {
  const response = await fetch('http://127.0.0.1:5002/api/messages');
  const messages = await response.json();
  return new Response(JSON.stringify(messages), {
    headers: { 'Content-Type': 'application/json' },
  });
}
