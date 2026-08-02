export type PublicSupabaseConfig = {
  url: string;
  publishableKey: string;
};

export function publicSupabaseConfig(): PublicSupabaseConfig {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !publishableKey) {
    throw new Error('A autenticação do piloto não está configurada.');
  }
  return { url, publishableKey };
}
