import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

export function middleware(req: NextRequest) {
  const url = req.nextUrl.clone();
  if (url.pathname.startsWith('/admin')) {
    const auth = req.headers.get('authorization');
    const expectedUser = process.env.NEXT_PUBLIC_ADMIN_USER || '';
    const expectedPass = process.env.NEXT_PUBLIC_ADMIN_PASS || '';
    if (!auth || !auth.startsWith('Basic ')) {
      const res = new NextResponse('Authentication required', { status: 401 });
      res.headers.set('WWW-Authenticate', 'Basic realm="Admin"');
      return res;
    }
    try {
      const [, b64] = auth.split(' ');
      const decoded = Buffer.from(b64, 'base64').toString('utf8');
      const [user, pass] = decoded.split(':');
      if (user !== expectedUser || pass !== expectedPass) {
        return new NextResponse('Forbidden', { status: 403 });
      }
    } catch {
      return new NextResponse('Forbidden', { status: 403 });
    }
  }
  return NextResponse.next();
}
