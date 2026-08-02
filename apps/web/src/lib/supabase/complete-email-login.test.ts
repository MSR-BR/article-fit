import type { SupabaseClient } from '@supabase/supabase-js';
import { describe, expect, it, vi } from 'vitest';
import { completeEmailLogin } from './complete-email-login';

function clientWith(auth: Record<string, ReturnType<typeof vi.fn>>) {
  return { auth } as unknown as SupabaseClient;
}

describe('completeEmailLogin', () => {
  it('exchanges a PKCE callback code for a session', async () => {
    const exchangeCodeForSession = vi.fn().mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const result = await completeEmailLogin(
      clientWith({ exchangeCodeForSession }),
      'https://article-fit.vercel.app/?code=callback-code',
    );
    expect(exchangeCodeForSession).toHaveBeenCalledWith('callback-code');
    expect(result).toEqual({
      email: 'pilot@example.com',
      callbackFound: true,
      error: false,
    });
  });

  it('verifies a token hash callback', async () => {
    const verifyOtp = vi.fn().mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const result = await completeEmailLogin(
      clientWith({ verifyOtp }),
      'https://article-fit.vercel.app/?token_hash=hashed-token',
    );
    expect(verifyOtp).toHaveBeenCalledWith({
      token_hash: 'hashed-token',
      type: 'email',
    });
    expect(result.callbackFound).toBe(true);
  });

  it('accepts an implicit access and refresh token callback', async () => {
    const setSession = vi.fn().mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const result = await completeEmailLogin(
      clientWith({ setSession }),
      'https://article-fit.vercel.app/#access_token=access&refresh_token=refresh',
    );
    expect(setSession).toHaveBeenCalledWith({
      access_token: 'access',
      refresh_token: 'refresh',
    });
    expect(result.email).toBe('pilot@example.com');
  });

  it('reuses an existing session when there is no callback', async () => {
    const getUser = vi.fn().mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const result = await completeEmailLogin(
      clientWith({ getUser }),
      'https://article-fit.vercel.app/',
    );
    expect(getUser).toHaveBeenCalledOnce();
    expect(result.callbackFound).toBe(false);
  });

  it('reports an invalid callback without inventing a session', async () => {
    const exchangeCodeForSession = vi.fn().mockResolvedValue({
      data: { user: null },
      error: new Error('expired'),
    });
    const result = await completeEmailLogin(
      clientWith({ exchangeCodeForSession }),
      'https://article-fit.vercel.app/?code=expired',
    );
    expect(result).toEqual({ email: null, callbackFound: true, error: true });
  });
});
