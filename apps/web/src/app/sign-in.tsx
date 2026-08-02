'use client';

import { FormEvent, useState } from 'react';
import { createClient } from '../lib/supabase/client';

export function SignIn({
  onSignedIn,
}: {
  onSignedIn: (email: string) => void;
}) {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function requestCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    const { error } = await createClient().auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: false },
    });
    setBusy(false);
    if (error) {
      setMessage(
        'Não foi possível enviar o código. Confirme se este e-mail foi convidado.',
      );
      return;
    }
    setCodeSent(true);
    setMessage('Código enviado. Verifique seu e-mail.');
  }

  async function verifyCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    const { data, error } = await createClient().auth.verifyOtp({
      email: email.trim(),
      token: code.trim(),
      type: 'email',
    });
    setBusy(false);
    if (error || !data.user?.email) {
      setMessage('Código inválido ou expirado. Solicite um novo código.');
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
          Use o e-mail autorizado. Enviaremos um código temporário, sem
          necessidade de senha.
        </p>
        {!codeSent ? (
          <form onSubmit={requestCode}>
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
              {busy ? 'Enviando…' : 'Receber código'}
            </button>
          </form>
        ) : (
          <form onSubmit={verifyCode}>
            <label htmlFor="pilot-code">Código recebido</label>
            <input
              id="pilot-code"
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(event) => setCode(event.currentTarget.value)}
              autoComplete="one-time-code"
              minLength={6}
              required
            />
            <button type="submit" disabled={busy || code.trim().length < 6}>
              {busy ? 'Verificando…' : 'Entrar'}
            </button>
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setCodeSent(false);
                setCode('');
                setMessage('');
              }}
            >
              Usar outro e-mail
            </button>
          </form>
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
