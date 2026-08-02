import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient } from '@supabase/supabase-js';
import { publicSupabaseConfig } from './config';

let browserClient: SupabaseClient | undefined;

export function createClient(): SupabaseClient {
  if (!browserClient) {
    const config = publicSupabaseConfig();
    browserClient = createBrowserClient(config.url, config.publishableKey);
  }
  return browserClient;
}
