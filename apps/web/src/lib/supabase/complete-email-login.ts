import type { SupabaseClient } from '@supabase/supabase-js';

export type EmailLoginResult = {
  email: string | null;
  callbackFound: boolean;
  error: boolean;
};

export async function completeEmailLogin(
  client: SupabaseClient,
  href: string,
): Promise<EmailLoginResult> {
  const url = new URL(href);
  const code = url.searchParams.get('code');
  const tokenHash = url.searchParams.get('token_hash');
  const hash = new URLSearchParams(url.hash.replace(/^#/, ''));
  const accessToken = hash.get('access_token');
  const refreshToken = hash.get('refresh_token');
  const callbackFound = Boolean(
    code || tokenHash || (accessToken && refreshToken),
  );

  if (code) {
    const { data, error } = await client.auth.exchangeCodeForSession(code);
    return {
      email: data.user?.email ?? null,
      callbackFound,
      error: Boolean(error),
    };
  }
  if (tokenHash) {
    const { data, error } = await client.auth.verifyOtp({
      token_hash: tokenHash,
      type: 'email',
    });
    return {
      email: data.user?.email ?? null,
      callbackFound,
      error: Boolean(error),
    };
  }
  if (accessToken && refreshToken) {
    const { data, error } = await client.auth.setSession({
      access_token: accessToken,
      refresh_token: refreshToken,
    });
    return {
      email: data.user?.email ?? null,
      callbackFound,
      error: Boolean(error),
    };
  }
  const { data, error } = await client.auth.getUser();
  return {
    email: data.user?.email ?? null,
    callbackFound,
    error: Boolean(error),
  };
}
