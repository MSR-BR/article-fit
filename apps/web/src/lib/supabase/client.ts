import { createBrowserClient } from '@supabase/ssr';
import {
  createClient as createSupabaseClient,
  type SupabaseClient,
} from '@supabase/supabase-js';
import { publicSupabaseConfig } from './config';

let browserClient: SupabaseClient | undefined;

export function createClient(): SupabaseClient {
  if (!browserClient) {
    const config = publicSupabaseConfig();
    browserClient = createBrowserClient(config.url, config.publishableKey);
  }
  return browserClient;
}

export function createEmailLinkClient(): SupabaseClient {
  const config = publicSupabaseConfig();
  return createSupabaseClient(config.url, config.publishableKey, {
    auth: {
      autoRefreshToken: false,
      detectSessionInUrl: false,
      flowType: 'implicit',
      persistSession: false,
    },
  });
}
