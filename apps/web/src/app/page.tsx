'use client';

import { ChangeEvent, useMemo, useRef, useState } from 'react';

type UploadState = {
  references: File[];
  manuscript: File | null;
};

const progressStages = [
  {
    key: 'project',
    label: 'Creating the analysis workspace',
    start: 0,
    end: 8,
    message: 'Creating a temporary workspace for this analysis.',
  },
  {
    key: 'uploads',
    label: 'Uploading and validating files',
    start: 8,
    end: 25,
    message:
      'Uploading the selected documents and validating their format and extractable content.',
  },
  {
    key: 'journal-resolution',
    label: 'Confirming the journal and official guidance',
    start: 25,
    end: 40,
    message:
      'Confirming the journal identity and validating the supplied official pages.',
  },
  {
    key: 'journal-research',
    label: 'Learning the journal editorial pattern',
    start: 40,
    end: 62,
    message:
      'Reviewing official guidance, recent articles, and the published editorial pattern.',
  },
  {
    key: 'manuscript-analysis',
    label: 'Comparing the manuscript with that pattern',
    start: 62,
    end: 78,
    message:
      'Checking structure, writing, content development, and scientific presentation.',
  },
  {
    key: 'ai-review',
    label: 'Preparing editorial suggestions',
    start: 78,
    end: 90,
    message:
      'Writing anchored suggestions and applying scientific-meaning safeguards.',
  },
  {
    key: 'artifact-generation',
    label: 'Generating and validating deliverables',
    start: 90,
    end: 100,
    message:
      'Generating the report and template-faithful PDF review, then validating each file.',
  },
] as const;

type RunState = 'idle' | 'running' | 'succeeded' | 'failed' | 'cancelled';

type RunContext = {
  controller: AbortController;
  projectId?: string;
  jobId?: string;
};

const emptyGuidance = {
  scopeUrl: '',
  guideUrl: '',
  scopeSnapshot: '',
  guideSnapshot: '',
};
const knownJournals = ['Physical Review Letters'];
// Vercel's serverless proxy rejects request bodies above roughly 4.5 MB.
const MAX_FILE_BYTES = 4 * 1024 * 1024;

type JobStatus = {
  state: string;
  stage: string;
  progress: number;
  errorCode?: string | null;
  errorDetail?: string | null;
};

type FeedbackStatus = {
  state: 'idle' | 'submitting' | 'complete' | 'error';
  message?: string;
};

function stageIndex(progress: number, backendStage?: string) {
  const exact = progressStages.findIndex((stage) => stage.key === backendStage);
  if (exact >= 0) return exact;
  const current = progressStages.findIndex((stage) => progress < stage.end);
  return current >= 0 ? current : progressStages.length - 1;
}

function sameOfficialDomain(scopeUrl: string, guideUrl: string) {
  try {
    const scope = new URL(scopeUrl);
    const guide = new URL(guideUrl);
    return (
      scope.protocol === 'https:' &&
      guide.protocol === 'https:' &&
      scope.hostname.toLowerCase() === guide.hostname.toLowerCase()
    );
  } catch {
    return false;
  }
}

function workflowError(job: JobStatus) {
  const code = job.errorCode ?? 'workflow-failed';
  return code.includes('502')
    ? 'Automatic journal lookup could not be completed. Wait a few minutes and try again. If it repeats, open “Only if automatic journal lookup fails” and provide the ISSN and official pages.'
    : code.includes('503')
      ? 'The service is temporarily unavailable. Wait a few minutes and try again.'
      : code.includes('422')
        ? 'Review the fields and uploaded files. One item could not be validated safely.'
        : code.includes('409')
          ? job.progress >= 34
            ? 'The analysis could not save an intermediate result. Reset the form and try again.'
            : 'Check that every required field and document was supplied, then try again.'
          : 'The analysis could not be completed. Check the fields and files, then try again in a few minutes.';
}

function requestError(status: number) {
  if (status === 413)
    return 'The upload service rejected this file because it is too large for the current connection. Select a PDF smaller than 4 MiB.';
  if (status === 415)
    return 'One file has an incompatible format. Use PDF for reference articles and PDF or Word for the manuscript.';
  if (status === 422)
    return 'Review the fields and uploaded files. One item could not be validated.';
  if (status === 409)
    return 'Check that every required field and document was supplied, then try again.';
  return 'The workflow cannot continue now. Wait a few minutes and try again.';
}

const artifactLabels: Record<string, string> = {
  'revision-report.pdf': 'Submission-fit report (PDF)',
  'revised-manuscript.pdf': 'Template-faithful manuscript review (PDF)',
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/journal-matcher${path}`, init);
  if (!response.ok) {
    throw new Error(requestError(response.status));
  }
  return response.json() as Promise<T>;
}

function FileSummary({ files }: { files: File[] }) {
  if (files.length === 0) return null;

  return (
    <ul className="file-list" aria-label="Selected files">
      {files.map((file) => (
        <li key={`${file.name}-${file.size}`}>
          <span>{file.name}</span>
          <small>{Math.max(1, Math.round(file.size / 1024))} KB</small>
        </li>
      ))}
    </ul>
  );
}

export default function HomePage() {
  const [uploads, setUploads] = useState<UploadState>({
    references: [],
    manuscript: null,
  });
  const [started, setStarted] = useState(false);
  const [journal, setJournal] = useState('');
  const [articleType, setArticleType] = useState('regular');
  const [journalIssn, setJournalIssn] = useState('');
  const [showProgress, setShowProgress] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [runState, setRunState] = useState<RunState>('idle');
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [feedbackStatus, setFeedbackStatus] = useState<
    Record<string, FeedbackStatus>
  >({});
  const [activePolicy, setActivePolicy] = useState<
    'ethics' | 'privacy' | 'support' | null
  >(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [guidance, setGuidance] = useState(emptyGuidance);
  const [inputVersion, setInputVersion] = useState(0);
  const runContext = useRef<RunContext | null>(null);
  const stopRequested = useRef(false);

  const activityMessage = reconnecting
    ? 'The server is still processing. Reconnecting to receive the latest confirmed status.'
    : (progressStages[activeStep]?.message ?? '');

  const manualValues = [guidance.scopeUrl, guidance.guideUrl].map((value) =>
    value.trim(),
  );
  const manualRequested = Boolean(
    journalIssn.trim() || manualValues.some(Boolean),
  );
  const officialUrlsReady = sameOfficialDomain(
    guidance.scopeUrl.trim(),
    guidance.guideUrl.trim(),
  );
  const assistedReady = manualValues.every(Boolean) && officialUrlsReady;
  const issnReady = /^\d{4}-\d{3}[\dXx]$/.test(journalIssn.trim());
  const manualReady = !manualRequested || (assistedReady && issnReady);

  const ready =
    journal.trim().length >= 2 &&
    uploads.references.length >= 3 &&
    uploads.manuscript !== null &&
    manualReady;
  const status = useMemo(() => {
    if (ready) {
      return started
        ? `Analysis started for ${journal.trim()}.`
        : 'Files are ready for analysis.';
    }
    if (!journal.trim()) return 'Enter the target journal to begin.';
    if (manualRequested && !manualReady) {
      return 'Complete all optional recovery fields, or clear them to use automatic discovery.';
    }
    if (uploads.references.length > 0 && uploads.references.length < 3) {
      return `Add at least ${3 - uploads.references.length} more reference article${uploads.references.length === 2 ? '' : 's'}.`;
    }
    if (uploads.references.length >= 3) {
      return 'Now upload the manuscript to be prepared for submission.';
    }
    if (uploads.manuscript) {
      return 'Now upload at least three articles published in the target journal.';
    }
    return 'Upload both sets of files to begin.';
  }, [journal, manualReady, manualRequested, ready, started, uploads]);

  async function startAnalysis() {
    if (!ready || !uploads.manuscript) return;
    const oversized = [...uploads.references, uploads.manuscript].filter(
      (file) => file.size > MAX_FILE_BYTES,
    );
    if (oversized.length) {
      setError(
        `Remove these files before starting: ${oversized.map((file) => `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MiB)`).join(', ')}. Each file must be smaller than 4 MiB (4,194,304 bytes).`,
      );
      // This is a client-side validation error, not a workflow failure.
      // Keep the form visible so the user can replace the file immediately.
      setRunState('idle');
      setStarted(false);
      setShowProgress(false);
      return;
    }
    const context: RunContext = { controller: new AbortController() };
    runContext.current = context;
    stopRequested.current = false;
    setActiveStep(0);
    setOverallProgress(2);
    setRunState('running');
    setStarted(true);
    setShowProgress(true);
    setError('');
    setArtifacts([]);
    setFeedback({});
    setFeedbackStatus({});
    setReconnecting(false);
    try {
      const project = await api<{ id: string }>('/projects', {
        method: 'POST',
        signal: context.controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ journalCandidate: journal.trim() }),
      });
      context.projectId = project.id;
      setActiveStep(1);
      setOverallProgress(8);
      const documents = [
        ...uploads.references
          .slice(0, 3)
          .map((file, index) => ({ file, slot: `reference-${index + 1}` })),
        { file: uploads.manuscript, slot: 'manuscript' },
      ];
      for (const [index, { file, slot }] of documents.entries()) {
        try {
          await api(
            `/projects/${project.id}/documents/${slot}?filename=${encodeURIComponent(file.name)}`,
            {
              method: 'PUT',
              signal: context.controller.signal,
              headers: {
                'Content-Type': 'application/octet-stream',
                'X-Document-Media-Type': file.type,
              },
              body: file,
            },
          );
        } catch (uploadError) {
          if (
            uploadError instanceof Error &&
            uploadError.message.includes('25 MB')
          ) {
            throw new Error(
              `The file “${file.name}” is too large for the current upload connection (${(file.size / 1024 / 1024).toFixed(2)} MiB). Select a file smaller than 4 MiB.`,
            );
          }
          throw uploadError;
        }
        setOverallProgress(
          8 + Math.round(((index + 1) / documents.length) * 17),
        );
      }
      setActiveStep(2);
      setOverallProgress(25);
      const initiated = await api<{
        analysisId?: string;
        artifacts?: Array<{ kind: string }>;
        id?: string;
        state?: string;
        progress?: number;
        errorCode?: string | null;
      }>(`/projects/${project.id}/run`, {
        method: 'POST',
        signal: context.controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idempotencyKey: crypto.randomUUID(),
          articleType,
          ...(manualRequested && manualReady
            ? {
                journalTitle: journal.trim(),
                journalIssn: journalIssn.trim().toUpperCase(),
                scopeUrl: guidance.scopeUrl,
                guideUrl: guidance.guideUrl,
                ...(guidance.scopeSnapshot.trim() &&
                guidance.guideSnapshot.trim()
                  ? {
                      scopeSnapshot: guidance.scopeSnapshot,
                      guideSnapshot: guidance.guideSnapshot,
                    }
                  : {}),
              }
            : {}),
        }),
      });
      let workflow = initiated;
      if (!workflow.analysisId && workflow.id) {
        context.jobId = workflow.id;
        let connectionFailures = 0;
        let lastConfirmedProgress = 25;
        let nextPollDelayMs = 2000;
        for (let attempt = 0; attempt < 300; attempt += 1) {
          let job: JobStatus;
          try {
            job = await api<JobStatus>(`/jobs/${workflow.id}`, {
              signal: context.controller.signal,
            });
            connectionFailures = 0;
            setReconnecting(false);
          } catch (pollError) {
            if (
              context.controller.signal.aborted ||
              (pollError instanceof DOMException &&
                pollError.name === 'AbortError')
            ) {
              throw pollError;
            }
            connectionFailures += 1;
            setReconnecting(true);
            if (connectionFailures >= 30) {
              throw new Error(
                'The connection could not be restored. The server may still be processing; wait a moment and try again.',
              );
            }
            await new Promise((resolve) => window.setTimeout(resolve, 2000));
            continue;
          }
          setOverallProgress((current) => Math.max(current, job.progress));
          setActiveStep((current) =>
            Math.max(current, stageIndex(job.progress, job.stage)),
          );
          if (job.progress > lastConfirmedProgress) {
            nextPollDelayMs = 2000;
          } else {
            nextPollDelayMs = Math.min(
              10000,
              Math.round(nextPollDelayMs * 1.5),
            );
          }
          lastConfirmedProgress = Math.max(lastConfirmedProgress, job.progress);
          if (job.state === 'failed' || job.state === 'cancelled') {
            throw new Error(workflowError(job));
          }
          if (job.state === 'succeeded') {
            const latest = await api<{
              id: string;
              artifacts: Array<{ kind: string }>;
            }>(`/projects/${project.id}/latest-analysis`, {
              signal: context.controller.signal,
            });
            workflow = {
              analysisId: latest.id,
              artifacts: latest.artifacts,
            };
            break;
          }
          await new Promise((resolve) =>
            window.setTimeout(resolve, nextPollDelayMs),
          );
        }
      }
      if (!workflow.analysisId || !workflow.artifacts) {
        throw new Error(
          'The analysis exceeded the monitoring window. Try again later.',
        );
      }
      setAnalysisId(workflow.analysisId);
      setArtifacts(
        workflow.artifacts
          .map((item) => item.kind)
          .filter((kind) => kind !== 'revised-manuscript.docx'),
      );
      setOverallProgress(100);
      setActiveStep(progressStages.length - 1);
      setRunState('succeeded');
      setStarted(false);
      setShowProgress(false);
      setReconnecting(false);
    } catch (caught) {
      if (stopRequested.current) return;
      setError(
        caught instanceof Error
          ? caught.message
          : 'The analysis could not be completed.',
      );
      setRunState('failed');
      setStarted(false);
      setReconnecting(false);
    } finally {
      if (runContext.current === context) runContext.current = null;
    }
  }

  async function stopAnalysis() {
    if (runState !== 'running') return;
    stopRequested.current = true;
    const context = runContext.current;
    context?.controller.abort();
    setRunState('cancelled');
    setStarted(false);
    setError('');
    try {
      if (context?.jobId) {
        await api(`/jobs/${context.jobId}/cancel`, { method: 'POST' });
      } else if (context?.projectId) {
        await fetch(`/api/journal-matcher/projects/${context.projectId}`, {
          method: 'DELETE',
        });
      }
    } catch {
      setError(
        'The analysis stopped on this screen. Any remaining temporary data will be removed automatically.',
      );
    }
  }

  function resetForm() {
    if (runState === 'running') return;
    setUploads({ references: [], manuscript: null });
    setJournal('');
    setArticleType('regular');
    setJournalIssn('');
    setGuidance(emptyGuidance);
    setStarted(false);
    setShowProgress(false);
    setActiveStep(0);
    setOverallProgress(0);
    setRunState('idle');
    setError('');
    setAnalysisId('');
    setArtifacts([]);
    setFeedback({});
    setFeedbackStatus({});
    setReconnecting(false);
    setInputVersion((current) => current + 1);
  }

  function hideProgress() {
    setShowProgress(false);
  }

  function selectReferences(event: ChangeEvent<HTMLInputElement>) {
    const references = Array.from(event.currentTarget.files ?? []);
    const oversized = references.filter((file) => file.size > MAX_FILE_BYTES);
    setUploads((current) => ({
      ...current,
      references,
    }));
    setError(
      oversized.length
        ? `Remove these files before starting: ${oversized.map((file) => `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`).join(', ')}.`
        : '',
    );
  }

  function selectManuscript(event: ChangeEvent<HTMLInputElement>) {
    const manuscript = event.currentTarget.files?.[0] ?? null;
    setUploads((current) => ({
      ...current,
      manuscript,
    }));
    setError(
      manuscript && manuscript.size > MAX_FILE_BYTES
        ? `Remove ${manuscript.name} (${(manuscript.size / 1024 / 1024).toFixed(2)} MiB) before starting. Each file must be smaller than 4 MiB (4,194,304 bytes).`
        : '',
    );
  }

  async function submitFeedback(kind: string) {
    const comment = feedback[kind]?.trim() ?? '';
    if (!analysisId || comment.length < 10) return;
    setFeedbackStatus((current) => ({
      ...current,
      [kind]: { state: 'submitting', message: 'Analyzing feedback…' },
    }));
    try {
      const result = await api<{
        applied: boolean;
        message: string;
        optimizationCount: number;
        feedbackCount: number;
      }>(`/analyses/${analysisId}/artifacts/${kind}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment }),
      });
      setFeedbackStatus((current) => ({
        ...current,
        [kind]: {
          state: 'complete',
          message: `${result.message} Journal memory: ${result.optimizationCount} optimization cycle${result.optimizationCount === 1 ? '' : 's'}, ${result.feedbackCount} feedback lesson${result.feedbackCount === 1 ? '' : 's'}.`,
        },
      }));
      setFeedback((current) => ({ ...current, [kind]: '' }));
    } catch (feedbackError) {
      setFeedbackStatus((current) => ({
        ...current,
        [kind]: {
          state: 'error',
          message:
            feedbackError instanceof Error
              ? feedbackError.message
              : 'Feedback could not be analyzed. Try again shortly.',
        },
      }));
    }
  }

  return (
    <main>
      <header className="brand" aria-label="Article Fit">
        <span className="brand-identity">
          <span className="brand-mark" aria-hidden="true">
            AF
          </span>
          <span>Article Fit</span>
        </span>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">Prepare your manuscript for the right journal</p>
        <h1 id="page-title">From draft to submission.</h1>
        <p className="lede">
          Enter the journal, upload reference articles and your manuscript.
          Article Fit learns the editorial pattern and delivers a review of both
          presentation and content. Uploaded documents are temporary and never
          become part of the journal memory.
        </p>
      </section>

      <section className="upload-panel" aria-label="Document upload">
        <div className="journal-block">
          <label htmlFor="target-journal">Target journal</label>
          <input
            id="target-journal"
            type="text"
            value={journal}
            onChange={(event) => setJournal(event.currentTarget.value)}
            placeholder="e.g. Physical Review Letters"
            autoComplete="organization"
            list="known-journals"
            required
          />
          <datalist id="known-journals">
            {knownJournals.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
          <small>
            The suggestions are journals already in Article Fit&apos;s profile
            database, with an editorial history. If your journal is not listed,
            type its name to add a new journal.
          </small>
        </div>

        <div className="article-type-block">
          <label htmlFor="article-type">Manuscript type</label>
          <select
            id="article-type"
            value={articleType}
            onChange={(event) => setArticleType(event.target.value)}
          >
            <option value="regular">Regular article</option>
            <option value="perspective">Perspective</option>
            <option value="review">Review</option>
            <option value="letter">Letter</option>
            <option value="other">Other</option>
          </select>
          <small>
            The selected type guides the structure, tone, and expected depth of
            the review.
          </small>
        </div>

        <div className="divider" aria-hidden="true" />

        <div className="upload-block">
          <div className="upload-copy">
            <span className="step">01</span>
            <div>
              <h2>Reference articles</h2>
              <p>Select three or more PDFs published in the target journal.</p>
            </div>
          </div>
          <label className="upload-button" htmlFor="reference-files">
            Select articles
          </label>
          <input
            key={`references-${inputVersion}`}
            id="reference-files"
            className="visually-hidden"
            type="file"
            accept="application/pdf,.pdf"
            multiple
            onChange={selectReferences}
          />
          <FileSummary files={uploads.references} />
          {uploads.references.length > 3 && (
            <small className="file-limit-notice">
              The MVP will process the first three PDFs; the remaining files
              will not be uploaded.
            </small>
          )}
        </div>

        <div className="divider" aria-hidden="true" />

        <div className="upload-block">
          <div className="upload-copy">
            <span className="step">02</span>
            <div>
              <h2>Your manuscript</h2>
              <p>Upload the manuscript as PDF or Word.</p>
            </div>
          </div>
          <label className="upload-button secondary" htmlFor="manuscript-file">
            Select manuscript
          </label>
          <input
            key={`manuscript-${inputVersion}`}
            id="manuscript-file"
            className="visually-hidden"
            type="file"
            accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
            onChange={selectManuscript}
          />
          <FileSummary files={uploads.manuscript ? [uploads.manuscript] : []} />
          <small className="file-limit-notice">
            Word preserves an editable template. With PDF, the PDF review keeps
            every original page intact and adds color-coded suggestion pages.
          </small>
        </div>
      </section>

      <details className="assisted-guidance">
        <summary>Only if automatic journal lookup fails</summary>
        <p>
          Normally, leave this closed. If Article Fit asks for help, provide the
          ISSN and both official pages. If the publisher blocks automated access
          (for example, with a Cloudflare challenge), paste the visible text of
          both pages below so the analysis can continue without guessing.
        </p>
        <div className="assisted-grid">
          <label>
            Journal ISSN
            <input
              type="text"
              value={journalIssn}
              onChange={(event) => setJournalIssn(event.currentTarget.value)}
              placeholder="e.g. 0031-9007"
            />
          </label>
          <label>
            Official Scope URL
            <input
              type="url"
              value={guidance.scopeUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  scopeUrl: value,
                }));
              }}
              placeholder="https://publisher.example/journal/scope"
            />
          </label>
          <label>
            Official Guide for Authors URL
            <input
              type="url"
              value={guidance.guideUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  guideUrl: value,
                }));
              }}
              placeholder="https://publisher.example/journal/authors"
            />
          </label>
          <label className="guidance-snapshot">
            Scope page text (only if the official page blocks access)
            <textarea
              value={guidance.scopeSnapshot}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  scopeSnapshot: value,
                }));
              }}
              placeholder="Paste the readable text from the official scope page."
              rows={5}
            />
          </label>
          <label className="guidance-snapshot">
            Guide for Authors text (only if the official page blocks access)
            <textarea
              value={guidance.guideSnapshot}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  guideSnapshot: value,
                }));
              }}
              placeholder="Paste the readable text from the official author guide."
              rows={5}
            />
          </label>
        </div>
        {manualRequested && !manualReady && (
          <small className="file-limit-notice">
            Complete all three fields, using official HTTPS pages from the same
            publisher domain, or clear them to return to automatic lookup.
          </small>
        )}
      </details>

      <p className={`status ${ready ? 'ready' : ''}`} role="status">
        <span aria-hidden="true" />
        {status}
      </p>

      <div className="primary-actions">
        <button
          className="analyze-button"
          type="button"
          disabled={!ready || started}
          onClick={startAnalysis}
        >
          {started ? 'Analysis in progress' : 'Start analysis'}
        </button>
        <button
          className="reset-button"
          type="button"
          disabled={runState === 'running'}
          onClick={resetForm}
        >
          Reset form
        </button>
      </div>

      {showProgress && (
        <div className="modal-backdrop">
          <section
            className="progress-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="progress-title"
            aria-describedby="progress-description"
          >
            <div className="progress-heading">
              <div>
                <p className="eyebrow">Confirmed workflow status</p>
                <h2 id="progress-title">
                  {runState === 'running' && (
                    <span className="spinner" aria-hidden="true" />
                  )}
                  {runState === 'failed' || runState === 'cancelled'
                    ? 'Analysis stopped'
                    : runState === 'succeeded'
                      ? 'Files ready'
                      : 'Preparing your manuscript'}
                </h2>
              </div>
              <button
                type="button"
                className="close-button"
                aria-label="Close progress dialog"
                onClick={hideProgress}
                disabled={runState === 'running'}
              >
                ×
              </button>
            </div>
            {runState === 'running' ? (
              <p
                id="progress-description"
                className="progress-description activity-line"
                aria-live="polite"
              >
                <strong>Current confirmed stage:</strong> {activityMessage}
              </p>
            ) : (
              <p id="progress-description" className="progress-description">
                {runState === 'succeeded'
                  ? 'Processing is complete and downloads are available.'
                  : runState === 'cancelled'
                    ? 'The analysis was stopped. You can adjust the fields and start again.'
                    : 'The analysis could not be completed. Follow the guidance below.'}
              </p>
            )}
            <div
              className="progress-track determinate"
              role="progressbar"
              aria-label="Milestone progress"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={overallProgress}
            >
              <span
                style={{
                  width: `${overallProgress}%`,
                }}
              />
            </div>
            <p className="overall-progress">
              Estimated milestone completion: {overallProgress}%. This value is
              based on confirmed workflow milestones, not elapsed time.
            </p>
            <ol className="progress-steps">
              {progressStages.map((stage, index) => {
                const state =
                  index < activeStep ||
                  (runState === 'succeeded' && index === activeStep)
                    ? 'complete'
                    : index === activeStep
                      ? error
                        ? 'error'
                        : runState === 'running'
                          ? 'active'
                          : ''
                      : '';
                const label =
                  state === 'complete'
                    ? 'Complete'
                    : state === 'active'
                      ? 'In progress'
                      : state === 'error'
                        ? 'Stopped here'
                        : 'Waiting';
                return (
                  <li className={state} key={stage.key}>
                    <span
                      className={state === 'active' ? 'step-spinner' : ''}
                      aria-hidden="true"
                    />
                    <div>
                      <strong>{stage.label}</strong>
                      <small>{label}</small>
                    </div>
                  </li>
                );
              })}
            </ol>
            {error && (
              <p className="preview-notice error" role="alert">
                {error}
              </p>
            )}
            {runState === 'running' && (
              <button
                className="stop-button"
                type="button"
                onClick={stopAnalysis}
              >
                Stop analysis
              </button>
            )}
            {runState === 'cancelled' && !error && (
              <p className="preview-notice" role="status">
                Analysis stopped. No final file was generated.
              </p>
            )}
            {runState === 'succeeded' && !error && (
              <p className="preview-notice" role="status">
                Analysis complete. The files are available below.
              </p>
            )}
          </section>
        </div>
      )}

      {error && !showProgress && (
        <p className="status error" role="alert">
          {error}
        </p>
      )}

      <section
        className={`results ${artifacts.length ? 'visible' : ''}`}
        aria-labelledby="results-title"
      >
        <div>
          <p className="eyebrow">Deliverables</p>
          <h2 id="results-title">Results</h2>
        </div>
        <p>
          {artifacts.length
            ? 'The analysis is complete. Download the generated deliverables below.'
            : 'When the analysis is complete, the deliverables will appear here.'}
        </p>
        {artifacts.length > 0 && (
          <div className="result-grid">
            {artifacts.map((kind) => {
              const status = feedbackStatus[kind] ?? { state: 'idle' };
              const fieldId = `feedback-${kind.replaceAll('.', '-')}`;
              return (
                <article key={kind} className="result-card">
                  <a
                    className="result-download"
                    href={`/api/journal-matcher/analyses/${analysisId}/artifacts/${kind}`}
                    download
                    aria-label={`Download ${artifactLabels[kind] ?? kind}`}
                  >
                    <span className="result-download-title">
                      {artifactLabels[kind] ?? kind}
                    </span>
                    <span className="download-action" aria-hidden="true">
                      <span className="download-icon">↓</span> Download file
                    </span>
                  </a>
                  <div className="artifact-feedback">
                    <label htmlFor={fieldId}>Feedback on this file</label>
                    <textarea
                      id={fieldId}
                      value={feedback[kind] ?? ''}
                      maxLength={4000}
                      placeholder="What should be improved in this deliverable?"
                      onChange={(event) =>
                        setFeedback((current) => ({
                          ...current,
                          [kind]: event.target.value,
                        }))
                      }
                    />
                    <button
                      type="button"
                      disabled={
                        (feedback[kind]?.trim().length ?? 0) < 10 ||
                        status.state === 'submitting'
                      }
                      onClick={() => void submitFeedback(kind)}
                    >
                      {status.state === 'submitting'
                        ? 'Analyzing…'
                        : 'Send feedback'}
                    </button>
                    {status.message && (
                      <small
                        className={`feedback-message ${status.state}`}
                        role={status.state === 'error' ? 'alert' : 'status'}
                      >
                        {status.message}
                      </small>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <footer>
        Original uploads are deleted after processing. Generated files remain
        available temporarily for up to 24 hours.
        <nav className="footer-links" aria-label="Information links">
          <button type="button" onClick={() => setActivePolicy('ethics')}>
            Ethics
          </button>
          <button type="button" onClick={() => setActivePolicy('privacy')}>
            Privacy
          </button>
          <button type="button" onClick={() => setActivePolicy('support')}>
            Support
          </button>
        </nav>
      </footer>
      {activePolicy && (
        <div
          className="policy-backdrop"
          onMouseDown={() => setActivePolicy(null)}
        >
          <section
            className="policy-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="policy-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              className="policy-close"
              type="button"
              aria-label="Close"
              onClick={() => setActivePolicy(null)}
            >
              ×
            </button>
            <h2 id="policy-title">
              {activePolicy === 'ethics'
                ? 'Ethics'
                : activePolicy === 'privacy'
                  ? 'Privacy'
                  : 'Support'}
            </h2>
            {activePolicy === 'ethics' && (
              <>
                <p>
                  Article Fit is an editorial support tool, not an author,
                  reviewer, or decision-maker. Authors remain responsible for
                  accuracy, originality, citations, authorship, disclosures, and
                  the final submission. Review the target journal&apos;s own AI
                  policy before submission.
                </p>
                <p>
                  AI-assisted text must be checked, rewritten where needed, and
                  disclosed when required. AI tools must never be listed as
                  authors, and scientific claims or references must not be
                  accepted without human verification.
                </p>
                <p className="policy-sources">
                  Reference guidance:{' '}
                  <a
                    href="https://publicationethics.org/cope-position-statements/ai-author"
                    target="_blank"
                    rel="noreferrer"
                  >
                    COPE
                  </a>
                  {' · '}
                  <a
                    href="https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html"
                    target="_blank"
                    rel="noreferrer"
                  >
                    ICMJE
                  </a>
                  {' · '}
                  <a
                    href="https://publishingsupport.iopscience.iop.org/questions/generative-ai-tools/"
                    target="_blank"
                    rel="noreferrer"
                  >
                    IOP Publishing
                  </a>
                </p>
              </>
            )}
            {activePolicy === 'privacy' && (
              <>
                <p>
                  Uploaded manuscripts and reference files are used only for the
                  requested analysis. Source uploads are deleted after
                  processing; generated files are temporary and may remain
                  available for up to 24 hours. The app does not retain a
                  personal archive of submitted manuscripts.
                </p>
                <p>
                  Article Fit may retain compact, journal-level editorial
                  lessons and official-source summaries to improve future
                  analyses. Do not upload confidential peer-review material or
                  data that you are not authorized to process. Check the target
                  journal&apos;s confidentiality rules before use.
                </p>
              </>
            )}
            {activePolicy === 'support' && (
              <p>
                For questions, report an error or request help at{' '}
                <a href="mailto:ai.agent.msrbr@gmail.com">
                  ai.agent.msrbr@gmail.com
                </a>
                .
              </p>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
