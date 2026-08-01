import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './styles.css';

export const metadata: Metadata = {
  title: 'Journal Matcher',
  description: 'Prepare seu manuscrito para o padrão editorial da revista certa.',
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
