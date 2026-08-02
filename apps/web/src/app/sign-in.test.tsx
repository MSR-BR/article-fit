import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SignIn } from './sign-in';

const { signInWithOtp, verifyOtp } = vi.hoisted(() => ({
  signInWithOtp: vi.fn(),
  verifyOtp: vi.fn(),
}));

vi.mock('../lib/supabase/client', () => ({
  createClient: () => ({ auth: { signInWithOtp, verifyOtp } }),
}));

describe('SignIn', () => {
  beforeEach(() => {
    signInWithOtp.mockReset();
    verifyOtp.mockReset();
  });

  it('requests a code only for an already provisioned email', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Receber código' }));
    await screen.findByText('Código enviado. Verifique seu e-mail.');
    expect(signInWithOtp).toHaveBeenCalledWith({
      email: 'pilot@example.com',
      options: { shouldCreateUser: false },
    });
    expect(screen.getByLabelText('Código recebido')).toBeInTheDocument();
  });

  it('verifies the email code and returns the named identity', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    verifyOtp.mockResolvedValue({
      data: { user: { email: 'pilot@example.com' } },
      error: null,
    });
    const onSignedIn = vi.fn();
    render(<SignIn onSignedIn={onSignedIn} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    await screen.findByLabelText('Código recebido');
    fireEvent.change(screen.getByLabelText('Código recebido'), {
      target: { value: '123456' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));
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

  it('handles an expired code and allows changing the email', async () => {
    signInWithOtp.mockResolvedValue({ error: null });
    verifyOtp.mockResolvedValue({
      data: { user: null },
      error: new Error('expired'),
    });
    render(<SignIn onSignedIn={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'pilot@example.com' },
    });
    fireEvent.submit(screen.getByLabelText('E-mail').closest('form')!);
    await screen.findByLabelText('Código recebido');
    fireEvent.change(screen.getByLabelText('Código recebido'), {
      target: { value: '123456' },
    });
    fireEvent.submit(screen.getByLabelText('Código recebido').closest('form')!);
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Código inválido ou expirado',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Usar outro e-mail' }));
    expect(screen.getByLabelText('E-mail')).toBeInTheDocument();
  });
});
