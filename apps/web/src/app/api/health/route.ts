import { healthResponseSchema } from '@journal-matcher/contracts';

export function GET() {
  const payload = healthResponseSchema.parse({
    service: 'web',
    status: 'ok',
    version: '0.1.0',
  });
  return Response.json(payload, { headers: { 'Cache-Control': 'no-store' } });
}
