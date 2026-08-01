import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import HomePage from './page';

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function completePackage() {
  fireEvent.change(screen.getByLabelText('Revista-alvo'), {
    target: { value: 'Physical Review Letters' },
  });
  fireEvent.change(screen.getByLabelText('Selecionar artigos'), {
    target: {
      files: [1, 2, 3].map((index) => new File(['pdf'], `referencia-${index}.pdf`, { type: 'application/pdf' })),
    },
  });
  fireEvent.change(screen.getByLabelText('Selecionar manuscrito'), {
    target: {
      files: [
        new File(['draft'], 'artigo.docx', {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }),
      ],
    },
  });
}

describe('HomePage', () => {
  afterEach(() => vi.unstubAllGlobals());
  it('shows only the two document inputs and the concise explanation', () => {
    render(<HomePage />);

    expect(screen.getByRole('heading', { name: 'Do rascunho à submissão.' })).toBeInTheDocument();
    expect(screen.getByLabelText('Selecionar artigos')).toHaveAttribute('multiple');
    expect(screen.getByLabelText('Selecionar manuscrito')).not.toHaveAttribute('multiple');
    expect(screen.getByLabelText('Revista-alvo')).toBeRequired();
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Informe a revista-alvo');
  });

  it('runs the real API sequence and reveals only returned artifacts', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({
          analysisId: 'analysis-1',
          artifacts: [
            { kind: 'revision-report.pdf' },
            { kind: 'revised-manuscript.docx' },
            { kind: 'revised-manuscript.pdf' },
          ],
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    const startButton = screen.getByRole('button', { name: 'Iniciar análise' });
    expect(startButton).toBeEnabled();
    fireEvent.click(startButton);
    expect(screen.getByRole('status')).toHaveTextContent('Análise iniciada');
    expect(screen.getByRole('dialog', { name: 'Preparando seu artigo' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Preparando seu artigo' }).querySelector('.spinner')).toBeInTheDocument();
    expect(screen.getByText('Criando o projeto').closest('li')).toHaveClass('active');
    await waitFor(() => expect(screen.getByText('Arquivos prontos').closest('li')).toHaveClass('active'));
    expect(screen.getByRole('link', { name: /Relatório de adequação/ })).toHaveAttribute(
      'href',
      '/api/journal-matcher/analyses/analysis-1/artifacts/revision-report.pdf',
    );
    expect(screen.getByRole('link', { name: /Artigo revisado \(Word\)/ })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(6);
  });

  it('asks for the remaining orientation articles', () => {
    render(<HomePage />);
    fireEvent.change(screen.getByLabelText('Revista-alvo'), {
      target: { value: 'Physical Review Letters' },
    });
    fireEvent.change(screen.getByLabelText('Selecionar artigos'), {
      target: { files: [new File(['pdf'], 'referencia.pdf', { type: 'application/pdf' })] },
    });
    expect(screen.getByRole('status')).toHaveTextContent('mais 2 artigos');
  });

  it('keeps analysis disabled until the target journal is informed', () => {
    render(<HomePage />);
    const references = [1, 2, 3].map(
      (index) => new File(['pdf'], `r-${index}.pdf`, { type: 'application/pdf' }),
    );
    fireEvent.change(screen.getByLabelText('Selecionar artigos'), { target: { files: references } });
    fireEvent.change(screen.getByLabelText('Selecionar manuscrito'), {
      target: { files: [new File(['draft'], 'artigo.pdf', { type: 'application/pdf' })] },
    });
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Informe a revista-alvo');
  });

  it('does not simulate progress while the backend has not answered', async () => {
    let resolveProject!: (value: Response) => void;
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>((resolve) => { resolveProject = resolve; })));
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar análise' }));
    expect(screen.getByText('Criando o projeto').closest('li')).toHaveClass('active');
    expect(screen.getByText('Enviando e validando os arquivos').closest('li')).not.toHaveClass('active');
    expect(screen.queryByRole('link', { name: /Baixar/ })).not.toBeInTheDocument();
    resolveProject(jsonResponse({ id: 'project-1' }));
    await waitFor(() => expect(screen.getByText('Enviando e validando os arquivos').closest('li')).toHaveClass('active'));
  });

  it('shows a recoverable backend error and enables another attempt', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ detail: 'Não foi possível confirmar a revista.' }, 422)),
    );
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Iniciar análise' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível confirmar a revista.');
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeEnabled();
    expect(screen.queryByRole('link', { name: /Baixar/ })).not.toBeInTheDocument();
  });

  it('requires a complete assisted official-guidance package', () => {
    render(<HomePage />);
    completePackage();
    fireEvent.change(screen.getByLabelText('URL oficial do escopo'), {
      target: { value: 'https://journals.aps.org/prl/about' },
    });
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Complete o pacote');
    fireEvent.change(screen.getByLabelText('URL oficial do guia dos autores'), {
      target: { value: 'https://journals.aps.org/prl/authors' },
    });
    fireEvent.change(screen.getByLabelText('Texto da página de escopo'), {
      target: { value: 'escopo oficial '.repeat(40) },
    });
    fireEvent.change(screen.getByLabelText('Texto do guia dos autores'), {
      target: { value: 'orientação oficial '.repeat(40) },
    });
    expect(screen.getByRole('button', { name: 'Iniciar análise' })).toBeEnabled();
  });
});
