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
      'Generating the report and color-coded review copies, then validating each file.',
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

type JobStatus = {
  state: string;
  stage: string;
  progress: number;
  errorCode?: string | null;
  errorDetail?: string | null;
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
    ? 'A required service could not be reached. Wait a few minutes and try again. If the problem continues, check the ISSN and official pages.'
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
  if (status === 413) return 'One file exceeds the 25 MB limit.';
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
  'revised-manuscript.docx': 'Color-coded manuscript review (Word)',
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
  const [journalIssn, setJournalIssn] = useState('');
  const [showProgress, setShowProgress] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [runState, setRunState] = useState<RunState>('idle');
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [guidance, setGuidance] = useState(emptyGuidance);
  const [inputVersion, setInputVersion] = useState(0);
  const runContext = useRef<RunContext | null>(null);
  const stopRequested = useRef(false);

  const activityMessage = progressStages[activeStep]?.message ?? '';

  const assistedValues = Object.values(guidance).map((value) => value.trim());
  const officialUrlsReady = sameOfficialDomain(
    guidance.scopeUrl.trim(),
    guidance.guideUrl.trim(),
  );
  const assistedReady =
    assistedValues.every(Boolean) &&
    officialUrlsReady &&
    guidance.scopeSnapshot.trim().length >= 500 &&
    guidance.guideSnapshot.trim().length >= 500;
  const issnReady = /^\d{4}-\d{3}[\dXx]$/.test(journalIssn.trim());

  const ready =
    journal.trim().length >= 2 &&
    issnReady &&
    uploads.references.length >= 3 &&
    uploads.manuscript !== null &&
    assistedReady;
  const status = useMemo(() => {
    if (ready) {
      return started
        ? `Analysis started for ${journal.trim()}.`
        : 'Files are ready for analysis.';
    }
    if (!journal.trim()) return 'Enter the target journal to begin.';
    if (!issnReady) return 'Enter the journal ISSN in the format 1234-567X.';
    if (!assistedReady) {
      return 'Complete the Scope and Guide for Authors using HTTPS URLs from the same official domain.';
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
  }, [assistedReady, issnReady, journal, ready, started, uploads]);

  async function startAnalysis() {
    if (!ready || !uploads.manuscript) return;
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
          journalTitle: journal.trim(),
          journalIssn: journalIssn.trim().toUpperCase(),
          ...guidance,
        }),
      });
      let workflow = initiated;
      if (!workflow.analysisId && workflow.id) {
        context.jobId = workflow.id;
        for (let attempt = 0; attempt < 300; attempt += 1) {
          const job = await api<JobStatus>(`/jobs/${workflow.id}`, {
            signal: context.controller.signal,
          });
          setOverallProgress((current) => Math.max(current, job.progress));
          setActiveStep((current) =>
            Math.max(current, stageIndex(job.progress, job.stage)),
          );
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
          await new Promise((resolve) => window.setTimeout(resolve, 2000));
        }
      }
      if (!workflow.analysisId || !workflow.artifacts) {
        throw new Error(
          'The analysis exceeded the monitoring window. Try again later.',
        );
      }
      setAnalysisId(workflow.analysisId);
      setArtifacts(workflow.artifacts.map((item) => item.kind));
      setOverallProgress(100);
      setActiveStep(progressStages.length - 1);
      setRunState('succeeded');
      setStarted(false);
      setShowProgress(false);
    } catch (caught) {
      if (stopRequested.current) return;
      setError(
        caught instanceof Error
          ? caught.message
          : 'The analysis could not be completed.',
      );
      setRunState('failed');
      setStarted(false);
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
    setInputVersion((current) => current + 1);
  }

  function hideProgress() {
    setShowProgress(false);
  }

  function selectReferences(event: ChangeEvent<HTMLInputElement>) {
    const references = Array.from(event.currentTarget.files ?? []);
    setUploads((current) => ({
      ...current,
      references,
    }));
  }

  function selectManuscript(event: ChangeEvent<HTMLInputElement>) {
    const manuscript = event.currentTarget.files?.[0] ?? null;
    setUploads((current) => ({
      ...current,
      manuscript,
    }));
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
            required
          />
          <small>Enter the journal&apos;s full name.</small>
          <label htmlFor="target-journal-issn">Journal ISSN</label>
          <input
            id="target-journal-issn"
            type="text"
            value={journalIssn}
            onChange={(event) => setJournalIssn(event.currentTarget.value)}
            placeholder="e.g. 0031-9007"
            inputMode="text"
            required
          />
          <small>
            The ISSN prevents unnecessary journal-identification requests.
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

      <section
        className="assisted-guidance"
        aria-labelledby="official-guidance-title"
      >
        <div className="upload-copy">
          <span className="step">03</span>
          <div>
            <h2 id="official-guidance-title">Official guidance</h2>
            <p>Scope and Guide for Authors are required.</p>
          </div>
        </div>
        <p>
          Enter the official pages and paste the visible text from each one.
          This reduces publisher blocking and speeds up the analysis.
        </p>
        <div className="assisted-grid">
          <label>
            Official Scope URL
            <input
              type="url"
              value={guidance.scopeUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({ ...current, scopeUrl: value }));
              }}
              placeholder="https://publisher.example/journal/scope"
              required
            />
          </label>
          <label>
            Official Guide for Authors URL
            <input
              type="url"
              value={guidance.guideUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({ ...current, guideUrl: value }));
              }}
              placeholder="https://publisher.example/journal/authors"
              required
            />
          </label>
          <label>
            Scope page text
            <textarea
              value={guidance.scopeSnapshot}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  scopeSnapshot: value,
                }));
              }}
              minLength={500}
              required
              placeholder="Paste at least 500 characters from the official page."
            />
          </label>
          <label>
            Guide for Authors text
            <textarea
              value={guidance.guideSnapshot}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({
                  ...current,
                  guideSnapshot: value,
                }));
              }}
              minLength={500}
              required
              placeholder="Paste at least 500 characters from the official page."
            />
          </label>
        </div>
        {!assistedReady && (
          <small className="file-limit-notice">
            Provide both URLs and at least 500 characters from each page.
          </small>
        )}
      </section>

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
            {artifacts.map((kind) => (
              <a
                key={kind}
                href={`/api/journal-matcher/analyses/${analysisId}/artifacts/${kind}`}
                download
              >
                <span>{artifactLabels[kind] ?? kind}</span>
                <small>Download file</small>
              </a>
            ))}
          </div>
        )}
      </section>

      <footer>
        Original uploads are deleted after processing. Generated files remain
        available temporarily for up to 24 hours.
      </footer>
    </main>
  );
}
