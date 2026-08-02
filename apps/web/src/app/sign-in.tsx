'use client';

import { FormEvent, useState } from 'react';
import { createClient, createEmailLinkClient } from '../lib/supabase/client';

export function SignIn({
  initialMessage = '',
  onSignedIn,
}: {
  initialMessage?: string;
  onSignedIn: (email: string) => void;
}) {
  const [email, setEmail] = useState('');
  const [linkSent, setLinkSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(initialMessage);

  async function requestLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    const { error } = await createEmailLinkClient().auth.signInWithOtp({
      email: email.trim(),
      options: {
        shouldCreateUser: false,
        emailRedirectTo: window.location.origin,
      },
    });
    setBusy(false);
    if (error) {
      if (error.code === 'over_email_send_rate_limit') {
        setMessage(
          'O limite temporário de e-mails do Supabase foi atingido. Aguarde uma hora desde os últimos envios e tente novamente.',
        );
      } else if (error.code === 'over_request_rate_limit') {
        setMessage(
          'Foram feitas muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente.',
        );
      } else {
        setMessage(
          'Não foi possível enviar o link. Confirme se este e-mail foi convidado.',
        );
      }
      return;
    }
    setLinkSent(true);
    setMessage('Link enviado. Verifique seu e-mail e abra o link para entrar.');
  }

  async function verifyAccess() {
    setBusy(true);
    const { data, error } = await createClient().auth.getUser();
    setBusy(false);
    if (error || !data.user?.email) {
      setMessage(
        'O acesso ainda não foi confirmado. Abra o link recebido ou solicite outro.',
      );
      return;
    }
    onSignedIn(data.user.email);
  }

  return (
    <main className="auth-shell">
      <header className="brand" aria-label="Article Fit">
        <span className="brand-mark" aria-hidden="true">
          AF
        </span>
        <span>Article Fit</span>
      </header>
      <section className="auth-card" aria-labelledby="auth-title">
        <p className="eyebrow">Piloto por convite</p>
        <h1 id="auth-title">Acesso ao Article Fit</h1>
        <p>
          Use o e-mail autorizado. Enviaremos um link seguro, sem necessidade de
          senha.
        </p>
        {!linkSent ? (
          <form onSubmit={requestLink}>
            <label htmlFor="pilot-email">E-mail</label>
            <input
              id="pilot-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.currentTarget.value)}
              autoComplete="email"
              required
            />
            <button type="submit" disabled={busy || !email.trim()}>
              {busy ? 'Enviando…' : 'Enviar link de acesso'}
            </button>
          </form>
        ) : (
          <div className="auth-link-actions">
            <button type="button" onClick={verifyAccess} disabled={busy}>
              {busy ? 'Verificando…' : 'Já abri o link'}
            </button>
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setLinkSent(false);
                setMessage('');
              }}
            >
              Usar outro e-mail
            </button>
          </div>
        )}
        {message && (
          <p className="auth-message" role="status">
            {message}
          </p>
        )}
      </section>
    </main>
  );
}
