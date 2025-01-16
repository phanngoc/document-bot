export async function DELETE(request, context) {
  const { id } = await context.params;
  console.log('DELETE:id', id);
  await fetch(`http://127.0.0.1:5002/api/assistants/${id}`, {
    method: 'DELETE',
  });
  return new Response(null, { status: 204 });
}
