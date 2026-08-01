import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import HomePage from './page';

describe('HomePage', () => {
  it('shows only the two document inputs and the concise explanation', () => {
    render(<HomePage />);

    expect(screen.getByRole('heading', { name: 'Do rascunho à submissão.' })).toBeInTheDocument();
    expect(screen.getByLabelText('Selecionar artigos')).toHaveAttribute('multiple');
    expect(screen.getByLabelText('Selecionar manuscrito')).not.toHaveAttribute('multiple');
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Envie os dois conjuntos');
  });

  it('recognizes a complete local upload package and reveals the outputs area', () => {
    render(<HomePage />);
    const references = [1, 2, 3].map(
      (index) => new File(['pdf'], `referencia-${index}.pdf`, { type: 'application/pdf' }),
    );
    const manuscript = new File(['draft'], 'artigo.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    fireEvent.change(screen.getByLabelText('Selecionar artigos'), {
      target: { files: references },
    });
    fireEvent.change(screen.getByLabelText('Selecionar manuscrito'), {
      target: { files: [manuscript] },
    });

    const startButton = screen.getByRole('button', { name: 'Iniciar análise' });
    expect(startButton).toBeEnabled();
    fireEvent.click(startButton);
    expect(screen.getByRole('status')).toHaveTextContent('Análise iniciada');
    expect(screen.getByRole('button', { name: 'Análise em andamento' })).toBeDisabled();
    expect(screen.getByText('Relatório de adequação')).toBeInTheDocument();
    expect(screen.getByText('Artigo revisado')).toBeInTheDocument();
  });

  it('asks for the remaining orientation articles', () => {
    render(<HomePage />);
    fireEvent.change(screen.getByLabelText('Selecionar artigos'), {
      target: { files: [new File(['pdf'], 'referencia.pdf', { type: 'application/pdf' })] },
    });
    expect(screen.getByRole('status')).toHaveTextContent('mais 2 artigos');
  });
});
