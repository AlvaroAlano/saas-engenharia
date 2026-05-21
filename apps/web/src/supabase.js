import { createClient } from '@supabase/supabase-js'

// Variáveis de ambiente importadas pelo Vite
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("ERRO: Variáveis VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY ausentes no .env!")
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
