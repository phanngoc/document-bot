export async function POST(request) {
    const data = await request.json();
    console.log('POST:data', data);
    const response = await fetch('http://127.0.0.1:5002/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...data,
        threadId: data.threadId
      }),
    });
    const jsonOutput = await response.json();
    return new Response(JSON.stringify(jsonOutput), {
      headers: { 'Content-Type': 'application/json' },
      status: 201,
    });
  }
