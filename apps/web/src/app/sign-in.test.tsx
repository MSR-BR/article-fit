import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SignIn } from './sign-in';

const { getUser, signInWithOtp } = vi.hoisted(() => ({
  getUser: vi.fn(),
  signInWithOtp: vi.fn(),
}));

vi.mock('../lib/supabase/client', () => ({
  createClient: () => ({ auth: { getUser } }),
  createEmailLinkClient: () => ({ auth: { signInWithOtp } }),
}));

describe('SignIn', () => {
  beforeEach(() => {
    signInWithOtp.mockReset();
    getUser.mockReset();
  });

  it('requests a magic link only for an already provisioned email', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Enviar link de acesso' }),
    );
    await screen.findByText(/Link enviado/);
    expect(signInWithOtp).toHaveBeenCalledWith({
      email: 'pilot@example.com',
      options: {
        shouldCreateUser: false,
        emailRedirectTo: window.location.origin,
      },
    });
    expect(
      screen.getByRole('button', { name: 'Já abri o link' }),
    ).toBeInTheDocument();
  });

  it('recognizes the session after the user opens the link', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    getUser.mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const onSignedIn = vi.fn();
    render(<SignIn onSignedIn={onSignedIn} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    fireEvent.click(
      await screen.findByRole('button', { name: 'Já abri o link' }),
    );
    await waitFor(() =>
      expect(onSignedIn).toHaveBeenCalledWith('pilot@example.com'),
    );
  });

  it('does not reveal whether an unprovisioned email exists', async () => {
    signInWithOtp.mockResolvedValue({ error: new Error('user not found') });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'unknown@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Confirme se este e-mail foi convidado',
    );
  });

  it('explains the temporary email quota instead of blaming the invitation', async () => {
    signInWithOtp.mockResolvedValue({
      error: { code: 'over_email_send_rate_limit' },
    });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    expect(await screen.findByRole('status')).toHaveTextContent(
      'limite temporário de e-mails',
    );
  });

  it('explains a burst of requests separately from the email quota', async () => {
    signInWithOtp.mockResolvedValue({
      error: { code: 'over_request_rate_limit' },
    });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    expect(await screen.findByRole('status')).toHaveTextContent(
      'muitas tentativas em pouco tempo',
    );
  });

  it('handles an unconfirmed link and allows changing the email', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    getUser.mockResolvedValue({
      data: { user: null },
      error: new Error('expired'),
    });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    fireEvent.click(
      await screen.findByRole('button', { name: 'Já abri o link' }),
    );
    expect(await screen.findByRole('status')).toHaveTextContent(
      'ainda não foi confirmado',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Usar outro e-mail' }));
    expect(screen.getByLabelText('E-mail')).toBeInTheDocument();
  });
});
