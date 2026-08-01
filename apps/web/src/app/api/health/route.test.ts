import { describe, expect, it } from 'vitest';
import { GET } from './route';

describe('web health route', () => {
  it('returns the shared health contract without caching', async () => {
    const response = GET();

    expect(response.headers.get('Cache-Control')).toBe('no-store');
    await expect(response.json()).resolves.toEqual({
      service: 'web',
      status: 'ok',
      version: '0.1.0',
    });
  });
});
