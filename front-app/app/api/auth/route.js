export async function POST(request) {
  const { username, password } = await request.json();
  
  // Kiểm tra thông tin đăng nhập (có thể kết nối đến cơ sở dữ liệu)
  if (username === 'admin' && password === 'password') {  // Thay đổi điều kiện này theo yêu cầu của bạn
    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } else {
    return new Response(JSON.stringify({ success: false }), { status: 401 });
  }
} 