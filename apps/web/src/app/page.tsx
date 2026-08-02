'use client';

import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';

type UploadState = {
  references: File[];
  manuscript: File | null;
};

const progressStages = [
  {
    key: 'project',
    label: 'Criando o projeto',
    start: 0,
    end: 8,
    messages: ['Criando uma área temporária e privada para esta análise.'],
  },
  {
    key: 'uploads',
    label: 'Enviando e validando os arquivos',
    start: 8,
    end: 25,
    messages: [
      'Enviando os documentos selecionados.',
      'Verificando formato, integridade e conteúdo extraível.',
    ],
  },
  {
    key: 'journal-resolution',
    label: 'Identificando a revista e as páginas oficiais',
    start: 25,
    end: 40,
    messages: [
      'Confirmando a identidade da revista informada.',
      'Localizando o escopo e o guia oficial dos autores.',
    ],
  },
  {
    key: 'journal-research',
    label: 'Estudando o padrão editorial da revista',
    start: 40,
    end: 62,
    messages: [
      'Lendo o escopo e o guia oficial dos autores.',
      'Buscando artigos recentes e versões abertas disponíveis.',
      'Comparando a arquitetura e a redação dos artigos publicados.',
    ],
  },
  {
    key: 'manuscript-analysis',
    label: 'Comparando seu artigo com o padrão encontrado',
    start: 62,
    end: 78,
    messages: [
      'Verificando estrutura, forma, conteúdo e apresentação científica.',
      'Localizando trechos que precisam de ajuste para a revista.',
    ],
  },
  {
    key: 'ai-review',
    label: 'Preparando as sugestões editoriais',
    start: 78,
    end: 90,
    messages: [
      'Redigindo sugestões ancoradas no texto original.',
      'Revisando as sugestões para evitar mudanças científicas indevidas.',
    ],
  },
  {
    key: 'artifact-generation',
    label: 'Gerando e validando os arquivos finais',
    start: 90,
    end: 100,
    messages: [
      'Gerando o relatório e o manuscrito com alterações destacadas.',
      'Validando os arquivos antes de liberar os downloads.',
    ],
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

function stagePercentage(
  stage: (typeof progressStages)[number],
  progress: number,
) {
  if (progress >= stage.end) return 100;
  if (progress <= stage.start) return 0;
  return Math.round(
    ((progress - stage.start) / (stage.end - stage.start)) * 100,
  );
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
    ? 'Não foi possível acessar um serviço necessário. Aguarde alguns minutos e tente novamente. Se o problema continuar, confira o ISSN e as páginas oficiais informadas.'
    : code.includes('503')
      ? 'O serviço está temporariamente indisponível. Aguarde alguns minutos e tente novamente.'
      : code.includes('422')
        ? 'Revise os campos e os arquivos enviados. Um deles não pôde ser validado com segurança.'
        : code.includes('409')
          ? 'Confira se todos os campos obrigatórios e documentos foram enviados e tente novamente.'
          : 'Não foi possível concluir a análise. Confira os campos e arquivos e tente novamente em alguns minutos.';
}

function requestError(status: number) {
  if (status === 413) return 'Um dos arquivos excede o limite de 25 MB.';
  if (status === 415)
    return 'Um dos arquivos está em formato incompatível. Use PDF nos artigos de orientação e PDF ou Word no manuscrito.';
  if (status === 422)
    return 'Revise os campos e os arquivos enviados. Um deles não pôde ser validado.';
  if (status === 409)
    return 'Confira se todos os campos obrigatórios e documentos foram enviados e tente novamente.';
  return 'Não foi possível continuar agora. Aguarde alguns minutos e tente novamente.';
}

const artifactLabels: Record<string, string> = {
  'revision-report.pdf': 'Relatório de adequação (PDF)',
  'revised-manuscript.docx': 'Artigo revisado (Word)',
  'revised-manuscript.pdf': 'Artigo revisado (PDF)',
  'provenance-manifest.json': 'Registro de fontes e processamento',
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
    <ul className="file-list" aria-label="Arquivos selecionados">
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
  const [activityIndex, setActivityIndex] = useState(0);
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [guidance, setGuidance] = useState(emptyGuidance);
  const [inputVersion, setInputVersion] = useState(0);
  const runContext = useRef<RunContext | null>(null);
  const stopRequested = useRef(false);

  const activeMessages = progressStages[activeStep]?.messages ?? [];
  const activityMessage =
    activeMessages[activityIndex % Math.max(activeMessages.length, 1)] ?? '';

  useEffect(() => {
    if (runState !== 'running' || activeMessages.length < 2) return;
    const timer = window.setInterval(() => {
      setActivityIndex((current) => current + 1);
    }, 3500);
    return () => window.clearInterval(timer);
  }, [activeStep, activeMessages.length, runState]);

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
        ? `Análise iniciada para ${journal.trim()}.`
        : 'Arquivos prontos para análise.';
    }
    if (!journal.trim()) return 'Informe a revista-alvo para iniciar.';
    if (!issnReady) return 'Informe o ISSN da revista no formato 1234-567X.';
    if (!assistedReady) {
      return 'Complete o Scope e o Guide for Authors com URLs HTTPS do mesmo domínio oficial.';
    }
    if (uploads.references.length > 0 && uploads.references.length < 3) {
      return `Adicione pelo menos mais ${3 - uploads.references.length} artigo${uploads.references.length === 2 ? '' : 's'} de orientação.`;
    }
    if (uploads.references.length >= 3) {
      return 'Agora envie o artigo que será preparado para submissão.';
    }
    if (uploads.manuscript) {
      return 'Agora envie pelo menos três artigos publicados na revista pretendida.';
    }
    return 'Envie os dois conjuntos de arquivos para iniciar.';
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
          'A análise excedeu o tempo de acompanhamento. Tente novamente mais tarde.',
        );
      }
      setAnalysisId(workflow.analysisId);
      setArtifacts(workflow.artifacts.map((item) => item.kind));
      setOverallProgress(100);
      setActiveStep(progressStages.length - 1);
      setRunState('succeeded');
      setStarted(false);
    } catch (caught) {
      if (stopRequested.current) return;
      setError(
        caught instanceof Error
          ? caught.message
          : 'Não foi possível concluir a análise.',
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
        'A análise parou nesta tela. Os dados temporários restantes serão eliminados automaticamente.',
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
    setActivityIndex(0);
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
        <p className="eyebrow">Prepare seu artigo para a revista certa</p>
        <h1 id="page-title">Do rascunho à submissão.</h1>
        <p className="lede">
          Informe a revista, envie artigos de orientação e o seu manuscrito. O
          Article Fit aprende o padrão editorial e entrega uma revisão de forma
          e conteúdo. Os documentos enviados são temporários e não entram na
          memória da revista.
        </p>
      </section>

      <section className="upload-panel" aria-label="Envio dos documentos">
        <div className="journal-block">
          <label htmlFor="target-journal">Revista-alvo</label>
          <input
            id="target-journal"
            type="text"
            value={journal}
            onChange={(event) => setJournal(event.currentTarget.value)}
            placeholder="Ex.: Physical Review Letters"
            autoComplete="organization"
            required
          />
          <small>Informe o nome completo da revista.</small>
          <label htmlFor="target-journal-issn">ISSN da revista</label>
          <input
            id="target-journal-issn"
            type="text"
            value={journalIssn}
            onChange={(event) => setJournalIssn(event.currentTarget.value)}
            placeholder="Ex.: 0031-9007"
            inputMode="text"
            required
          />
          <small>
            O ISSN evita consultas desnecessárias para identificar a revista.
          </small>
        </div>

        <div className="divider" aria-hidden="true" />

        <div className="upload-block">
          <div className="upload-copy">
            <span className="step">01</span>
            <div>
              <h2>Artigos de orientação</h2>
              <p>Selecione três ou mais PDFs publicados na revista-alvo.</p>
            </div>
          </div>
          <label className="upload-button" htmlFor="reference-files">
            Selecionar artigos
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
              O MVP processará os três primeiros PDFs; os demais não serão
              enviados.
            </small>
          )}
        </div>

        <div className="divider" aria-hidden="true" />

        <div className="upload-block">
          <div className="upload-copy">
            <span className="step">02</span>
            <div>
              <h2>Seu artigo</h2>
              <p>Envie o manuscrito em PDF ou Word.</p>
            </div>
          </div>
          <label className="upload-button secondary" htmlFor="manuscript-file">
            Selecionar manuscrito
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
        </div>
      </section>

      <section
        className="assisted-guidance"
        aria-labelledby="official-guidance-title"
      >
        <div className="upload-copy">
          <span className="step">03</span>
          <div>
            <h2 id="official-guidance-title">Orientação oficial</h2>
            <p>Scope e Guide for Authors são obrigatórios.</p>
          </div>
        </div>
        <p>
          Informe as páginas oficiais e cole o texto visível de cada uma. Isso
          reduz bloqueios das editoras e acelera a análise.
        </p>
        <div className="assisted-grid">
          <label>
            URL oficial do escopo
            <input
              type="url"
              value={guidance.scopeUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({ ...current, scopeUrl: value }));
              }}
              placeholder="https://editora.example/revista/scope"
              required
            />
          </label>
          <label>
            URL oficial do guia dos autores
            <input
              type="url"
              value={guidance.guideUrl}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setGuidance((current) => ({ ...current, guideUrl: value }));
              }}
              placeholder="https://editora.example/revista/authors"
              required
            />
          </label>
          <label>
            Texto da página de escopo
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
              placeholder="Cole ao menos 500 caracteres da página oficial."
            />
          </label>
          <label>
            Texto do guia dos autores
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
              placeholder="Cole ao menos 500 caracteres da página oficial."
            />
          </label>
        </div>
        {!assistedReady && (
          <small className="file-limit-notice">
            Preencha as duas URLs e pelo menos 500 caracteres de cada página.
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
          {started ? 'Análise em andamento' : 'Iniciar análise'}
        </button>
        <button
          className="reset-button"
          type="button"
          disabled={runState === 'running'}
          onClick={resetForm}
        >
          Limpar campos
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
                <p className="eyebrow">Andamento real</p>
                <h2 id="progress-title">
                  {runState === 'running' && (
                    <span className="spinner" aria-hidden="true" />
                  )}
                  {runState === 'failed' || runState === 'cancelled'
                    ? 'Análise interrompida'
                    : runState === 'succeeded'
                      ? 'Arquivos prontos'
                      : 'Preparando seu artigo'}
                </h2>
              </div>
              <button
                type="button"
                className="close-button"
                aria-label="Fechar acompanhamento"
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
                <strong>Agora:</strong> {activityMessage}
              </p>
            ) : (
              <p id="progress-description" className="progress-description">
                {runState === 'succeeded'
                  ? 'Processamento concluído e downloads liberados.'
                  : runState === 'cancelled'
                    ? 'A análise foi interrompida. Você pode ajustar os campos e iniciar novamente.'
                    : 'Não foi possível concluir. Siga a orientação abaixo.'}
              </p>
            )}
            <div
              className="progress-track determinate"
              role="progressbar"
              aria-label="Andamento da análise"
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
              Progresso geral: aproximadamente {overallProgress}%
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
                const percentage = stagePercentage(stage, overallProgress);
                const label = `${percentage}%${index === activeStep && runState === 'running' ? ' aprox.' : ''}`;
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
                Parar análise
              </button>
            )}
            {runState === 'cancelled' && !error && (
              <p className="preview-notice" role="status">
                Análise interrompida. Nenhum arquivo final foi gerado.
              </p>
            )}
            {runState === 'succeeded' && !error && (
              <p className="preview-notice" role="status">
                Análise concluída. Os arquivos estão disponíveis abaixo.
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
          <p className="eyebrow">Saídas</p>
          <h2 id="results-title">Resultados</h2>
        </div>
        <p>
          {artifacts.length
            ? 'A análise terminou. Baixe os produtos gerados abaixo.'
            : 'Quando a análise terminar, os produtos aparecerão aqui para download.'}
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
                <small>Baixar arquivo</small>
              </a>
            ))}
          </div>
        )}
      </section>

      <footer>
        Os originais são eliminados após o processamento. Os arquivos de saída
        ficam disponíveis temporariamente por até 24 horas.
      </footer>
    </main>
  );
}
