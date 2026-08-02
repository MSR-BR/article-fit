export function GET() {
  const payload = {
    service: 'web',
    status: 'ok',
    version: '0.1.0',
  } as const;
  return Response.json(payload, { headers: { 'Cache-Control': 'no-store' } });
}
