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
  fireEvent.change(screen.getByLabelText('Target journal'), {
    target: { value: 'Physical Review Letters' },
  });
  fireEvent.change(screen.getByLabelText('Select articles'), {
    target: {
      files: [1, 2, 3].map(
        (index) =>
          new File(['pdf'], `referencia-${index}.pdf`, {
            type: 'application/pdf',
          }),
      ),
    },
  });
  fireEvent.change(screen.getByLabelText('Select manuscript'), {
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

  it('opens the MVP upload interface without a login gate', () => {
    render(<HomePage />);
    expect(
      screen.getByRole('heading', { name: 'From draft to submission.' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Target journal')).toBeInTheDocument();
    expect(screen.queryByText(/Acesso ao Article Fit/)).not.toBeInTheDocument();
  });
  it('requires only the journal, manuscript, and reference articles', () => {
    render(<HomePage />);

    expect(
      screen.getByRole('heading', { name: 'From draft to submission.' }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Select articles')).toHaveAttribute(
      'multiple',
    );
    expect(screen.getByLabelText('Select manuscript')).not.toHaveAttribute(
      'multiple',
    );
    expect(screen.getByLabelText('Target journal')).toBeRequired();
    expect(screen.getByLabelText('Journal ISSN')).not.toBeRequired();
    expect(screen.getByLabelText('Official Scope URL')).not.toBeRequired();
    expect(
      screen.getByLabelText('Official Guide for Authors URL'),
    ).not.toBeRequired();
    expect(
      screen.getByText('Only if automatic journal lookup fails'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Enter the target journal',
    );
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

    const startButton = screen.getByRole('button', { name: 'Start analysis' });
    expect(startButton).toBeEnabled();
    fireEvent.click(startButton);
    expect(screen.getByRole('status')).toHaveTextContent('Analysis started');
    expect(
      screen.getByRole('dialog', { name: 'Preparing your manuscript' }),
    ).toBeInTheDocument();
    expect(
      screen
        .getByRole('heading', { name: 'Preparing your manuscript' })
        .querySelector('.spinner'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Creating the analysis workspace').closest('li'),
    ).toHaveClass('active');
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(
      screen.getByRole('link', { name: /Submission-fit report/ }),
    ).toHaveAttribute(
      'href',
      '/api/journal-matcher/analyses/analysis-1/artifacts/revision-report.pdf',
    );
    expect(
      screen.queryByText(/Color-coded manuscript review \(Word\)/),
    ).toBeNull();
    expect(
      screen.getByRole('link', { name: /Template-faithful manuscript review/ }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(6);
    expect(JSON.parse(String(fetchMock.mock.calls[5]?.[1]?.body))).toEqual({
      idempotencyKey: expect.any(String),
      articleType: 'regular',
    });
  });

  it('submits independent feedback for a generated artifact', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-feedback' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({
          analysisId: 'analysis-feedback',
          artifacts: [{ kind: 'revision-report.pdf' }],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          applied: true,
          message:
            'Feedback analyzed and incorporated as advisory guidance for future outputs.',
          optimizationCount: 3,
          feedbackCount: 1,
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    await screen.findByRole('link', { name: /Submission-fit report/ });
    const field = screen.getByLabelText('Feedback on this file');
    fireEvent.change(field, {
      target: {
        value:
          'The report should include more concrete scientific validation actions.',
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send feedback' }));

    expect(
      await screen.findByText(
        /Journal memory: 3 optimization cycles, 1 feedback lesson/,
      ),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/journal-matcher/analyses/analysis-feedback/artifacts/revision-report.pdf/feedback',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('uses the latest analysis id after an asynchronous job succeeds', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-async' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'job-1', state: 'queued' }))
      .mockResolvedValueOnce(
        jsonResponse({
          state: 'succeeded',
          stage: 'artifacts-ready',
          progress: 100,
          errorCode: null,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: 'analysis-async',
          artifacts: [{ kind: 'revision-report.pdf' }],
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    expect(
      await screen.findByRole('link', { name: /Submission-fit report/ }),
    ).toHaveAttribute(
      'href',
      '/api/journal-matcher/analyses/analysis-async/artifacts/revision-report.pdf',
    );
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.queryByText('Continuar em segundo plano')).toBeNull();
    expect(document.querySelector('.spinner')).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(8);
  });

  it('explains a failed backend stage and stops every spinner', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-failed' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({ id: 'job-failed', state: 'queued' }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          state: 'failed',
          stage: 'ai-review',
          progress: 82,
          errorCode: 'workflow-502',
          errorDetail: 'O provedor de IA não respondeu dentro do limite.',
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Wait a few minutes and try again',
    );
    expect(screen.getByRole('alert')).not.toHaveTextContent('workflow-502');
    expect(screen.getByRole('alert')).not.toHaveTextContent('provedor de IA');
    expect(
      screen.getByRole('dialog', { name: 'Analysis stopped' }),
    ).toBeInTheDocument();
    expect(screen.queryByText('Continuar em segundo plano')).toBeNull();
    expect(document.querySelector('.spinner')).toBeNull();
    expect(document.querySelector('.step-spinner')).toBeNull();
  });

  it('does not blame missing inputs for a persistence conflict after research', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-conflict' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({ id: 'job-conflict', state: 'queued' }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          state: 'failed',
          stage: 'manuscript-analysis',
          progress: 62,
          errorCode: 'workflow-409',
          errorDetail: 'Hosted persistence conflict',
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'could not save an intermediate result',
    );
    expect(screen.getByRole('alert')).not.toHaveTextContent(
      'every required field',
    );
    expect(screen.getByRole('alert')).not.toHaveTextContent(
      'Hosted persistence conflict',
    );
  });

  it('shows milestone-based progress and one confirmed activity while running', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => {})),
    );
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    expect(
      screen.getByText(/Estimated milestone completion: 2%/),
    ).toBeInTheDocument();
    expect(screen.getByText('Current confirmed stage:')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '2',
    );
  });

  it('never moves progress backwards when a queued job still reports zero', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-monotonic' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({ id: 'job-monotonic', state: 'queued' }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          state: 'queued',
          stage: 'awaiting-worker',
          progress: 0,
          errorCode: null,
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '25',
    );
    expect(
      screen.getByText(/Estimated milestone completion: 25%/),
    ).toBeInTheDocument();
  });

  it('keeps confirmed progress and reconnects after a polling interruption', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-reconnect' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({ id: 'job-reconnect', state: 'queued' }),
      )
      .mockRejectedValueOnce(new TypeError('Network connection lost'));
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();

    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));

    expect(
      await screen.findByText(
        /Reconnecting to receive the latest confirmed status/,
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute(
      'aria-valuenow',
      '25',
    );
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('cancels a created job and stops the visible analysis', async () => {
    const pendingJob = new Promise<Response>(() => {});
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-stop' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'job-stop', state: 'queued' }))
      .mockImplementationOnce(() => pendingJob)
      .mockResolvedValueOnce(
        jsonResponse({ state: 'cancelled', stage: 'cancelled', progress: 25 }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));

    fireEvent.click(screen.getByRole('button', { name: 'Stop analysis' }));

    expect(
      await screen.findByRole('dialog', { name: 'Analysis stopped' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/No final file was generated/)).toBeInTheDocument();
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/journal-matcher/jobs/job-stop/cancel',
        expect.objectContaining({ method: 'POST' }),
      ),
    );
    expect(document.querySelector('.spinner')).toBeNull();
  });

  it('clears every field and allows the same files to be selected again', () => {
    render(<HomePage />);
    completePackage();
    expect(screen.getByText('referencia-1.pdf')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reset form' }));

    expect(screen.getByLabelText('Target journal')).toHaveValue('');
    expect(screen.getByLabelText('Journal ISSN')).toHaveValue('');
    expect(screen.getByLabelText('Official Scope URL')).toHaveValue('');
    expect(screen.queryByText('referencia-1.pdf')).toBeNull();
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeDisabled();
  });

  it('asks for the remaining orientation articles', () => {
    render(<HomePage />);
    completePackage();
    fireEvent.change(screen.getByLabelText('Select articles'), {
      target: {
        files: [
          new File(['pdf'], 'referencia.pdf', { type: 'application/pdf' }),
        ],
      },
    });
    expect(screen.getByRole('status')).toHaveTextContent(
      '2 more reference articles',
    );
  });

  it('keeps analysis disabled until the target journal is informed', () => {
    render(<HomePage />);
    const references = [1, 2, 3].map(
      (index) =>
        new File(['pdf'], `r-${index}.pdf`, { type: 'application/pdf' }),
    );
    fireEvent.change(screen.getByLabelText('Select articles'), {
      target: { files: references },
    });
    fireEvent.change(screen.getByLabelText('Select manuscript'), {
      target: {
        files: [new File(['draft'], 'artigo.pdf', { type: 'application/pdf' })],
      },
    });
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Enter the target journal',
    );
  });

  it('does not simulate progress while the backend has not answered', async () => {
    let resolveProject!: (value: Response) => void;
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            resolveProject = resolve;
          }),
      ),
    );
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));
    expect(
      screen.getByText('Creating the analysis workspace').closest('li'),
    ).toHaveClass('active');
    expect(
      screen.getByText('Uploading and validating files').closest('li'),
    ).not.toHaveClass('active');
    expect(
      screen.queryByRole('link', { name: /Download/ }),
    ).not.toBeInTheDocument();
    resolveProject(jsonResponse({ id: 'project-1' }));
    await waitFor(() =>
      expect(
        screen.getByText('Uploading and validating files').closest('li'),
      ).toHaveClass('active'),
    );
  });

  it('shows a recoverable backend error and enables another attempt', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ detail: 'The journal could not be confirmed.' }, 422),
        ),
    );
    render(<HomePage />);
    completePackage();
    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The journal could not be confirmed.',
    );
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeEnabled();
    expect(
      screen.queryByRole('link', { name: /Download/ }),
    ).not.toBeInTheDocument();
  });

  it('requires a complete optional recovery package only when one field is used', () => {
    render(<HomePage />);
    completePackage();
    fireEvent.change(screen.getByLabelText('Journal ISSN'), {
      target: { value: '0031-9007' },
    });
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(
      'Complete all optional recovery fields',
    );
    fireEvent.change(screen.getByLabelText('Official Scope URL'), {
      target: { value: 'https://journals.aps.org/prl/about' },
    });
    fireEvent.change(screen.getByLabelText('Official Guide for Authors URL'), {
      target: { value: 'https://journals.aps.org/prl/authors' },
    });
    expect(
      screen.getByRole('button', { name: 'Start analysis' }),
    ).toBeEnabled();
  });

  it('sends optional verified identity only when manual recovery is complete', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'project-manual' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-2' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'reference-3' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'manuscript' }))
      .mockResolvedValueOnce(
        jsonResponse({ analysisId: 'analysis-manual', artifacts: [] }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<HomePage />);
    completePackage();
    fireEvent.change(screen.getByLabelText('Journal ISSN'), {
      target: { value: '0031-9007' },
    });
    fireEvent.change(screen.getByLabelText('Official Scope URL'), {
      target: { value: 'https://journals.aps.org/prl/about' },
    });
    fireEvent.change(screen.getByLabelText('Official Guide for Authors URL'), {
      target: { value: 'https://journals.aps.org/prl/authors' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start analysis' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6));
    expect(
      JSON.parse(String(fetchMock.mock.calls[5]?.[1]?.body)),
    ).toMatchObject({
      journalTitle: 'Physical Review Letters',
      journalIssn: '0031-9007',
      scopeUrl: 'https://journals.aps.org/prl/about',
      guideUrl: 'https://journals.aps.org/prl/authors',
    });
  });

  it('opens policy dialogs and closes them with the close button or backdrop', () => {
    render(<HomePage />);

    fireEvent.click(screen.getByRole('button', { name: 'Ethics' }));
    expect(screen.getByRole('dialog', { name: 'Ethics' })).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole('dialog').parentElement!);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Privacy' }));
    expect(screen.getByRole('dialog', { name: 'Privacy' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));

    fireEvent.click(screen.getByRole('button', { name: 'Support' }));
    expect(screen.getByRole('dialog', { name: 'Support' })).toBeInTheDocument();
  });

  it('accepts browser-assisted official page text when publishers block access', () => {
    render(<HomePage />);
    fireEvent.change(screen.getByLabelText('Target journal'), {
      target: { value: 'Physical Review Letters' },
    });
    fireEvent.change(screen.getByLabelText('Journal ISSN'), {
      target: { value: '0031-9007' },
    });
    fireEvent.change(screen.getByLabelText('Official Scope URL'), {
      target: { value: 'https://journals.aps.org/prl/about' },
    });
    fireEvent.change(screen.getByLabelText('Official Guide for Authors URL'), {
      target: { value: 'https://journals.aps.org/prl/authors' },
    });
    fireEvent.change(screen.getByLabelText(/Scope page text/), {
      target: { value: 'Official scope text copied from the publisher.' },
    });
    fireEvent.change(screen.getByLabelText(/Guide for Authors text/), {
      target: {
        value: 'Official author guide text copied from the publisher.',
      },
    });
    expect(screen.getByLabelText(/Scope page text/)).toHaveValue(
      'Official scope text copied from the publisher.',
    );
    expect(screen.getByLabelText(/Guide for Authors text/)).toHaveValue(
      'Official author guide text copied from the publisher.',
    );
  });
});
