'use client';

import { ChangeEvent, useEffect, useMemo, useState } from 'react';

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

type RunState = 'idle' | 'running' | 'succeeded' | 'failed';

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

function workflowError(job: JobStatus) {
  const code = job.errorCode ?? 'workflow-failed';
  const stage =
    progressStages[stageIndex(job.progress, job.stage)]?.label.toLowerCase() ??
    'processamento';
  const explanation = code.includes('502')
    ? 'Um serviço externo de pesquisa ou de inteligência artificial respondeu com um erro temporário.'
    : code.includes('503')
      ? 'Um serviço necessário estava temporariamente indisponível.'
      : code.includes('422')
        ? 'O conteúdo recebido não pôde ser validado com segurança.'
        : code.includes('409')
          ? 'Faltaram dados ou evidências necessários para continuar com segurança.'
          : 'O processamento foi interrompido antes da geração dos arquivos.';
  const detail = job.errorDetail?.trim()
    ? ` Motivo informado pelo servidor: ${job.errorDetail.trim()}`
    : '';
  return `${explanation}${detail} Etapa: ${stage}. Erro técnico: ${code}.`;
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
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload.detail === 'string'
        ? payload.detail
        : payload.detail?.message;
    throw new Error(detail || `A operação falhou (${response.status}).`);
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
  const [showProgress, setShowProgress] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [runState, setRunState] = useState<RunState>('idle');
  const [activityIndex, setActivityIndex] = useState(0);
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [guidance, setGuidance] = useState({
    scopeUrl: '',
    guideUrl: '',
    scopeSnapshot: '',
    guideSnapshot: '',
  });

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
  const assistedStarted = assistedValues.some(Boolean);
  const assistedReady =
    assistedValues.every(Boolean) &&
    guidance.scopeSnapshot.trim().length >= 500 &&
    guidance.guideSnapshot.trim().length >= 500;

  const ready =
    journal.trim().length >= 2 &&
    uploads.references.length >= 3 &&
    uploads.manuscript !== null &&
    (!assistedStarted || assistedReady);
  const status = useMemo(() => {
    if (assistedStarted && !assistedReady) {
      return 'Complete o pacote de orientação oficial assistida para iniciar.';
    }
    if (ready) {
      return started
        ? `Análise iniciada para ${journal.trim()}.`
        : 'Arquivos prontos para análise.';
    }
    if (!journal.trim()) return 'Informe a revista-alvo para iniciar.';
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
  }, [assistedReady, assistedStarted, journal, ready, started, uploads]);

  async function startAnalysis() {
    if (!ready || !uploads.manuscript) return;
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ journalCandidate: journal.trim() }),
      });
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idempotencyKey: crypto.randomUUID(),
          ...(assistedReady ? guidance : {}),
        }),
      });
      let workflow = initiated;
      if (!workflow.analysisId && workflow.id) {
        for (let attempt = 0; attempt < 300; attempt += 1) {
          const job = await api<JobStatus>(`/jobs/${workflow.id}`);
          setOverallProgress(job.progress);
          setActiveStep(stageIndex(job.progress, job.stage));
          if (job.state === 'failed' || job.state === 'cancelled') {
            throw new Error(workflowError(job));
          }
          if (job.state === 'succeeded') {
            const latest = await api<{
              id: string;
              artifacts: Array<{ kind: string }>;
            }>(`/projects/${project.id}/latest-analysis`);
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
      setError(
        caught instanceof Error
          ? caught.message
          : 'Não foi possível concluir a análise.',
      );
      setRunState('failed');
      setStarted(false);
    }
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
          <small>Informe o título, ISSN ou endereço oficial da revista.</small>
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
            id="manuscript-file"
            className="visually-hidden"
            type="file"
            accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
            onChange={selectManuscript}
          />
          <FileSummary files={uploads.manuscript ? [uploads.manuscript] : []} />
        </div>
      </section>

      <details className="assisted-guidance">
        <summary>A editora bloqueia a consulta automática?</summary>
        <p>
          Informe as páginas oficiais e cole o texto visível delas. Use somente
          quando o aplicativo indicar bloqueio.
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
            />
          </label>
        </div>
        {assistedStarted && !assistedReady && (
          <small className="file-limit-notice">
            Preencha as duas URLs e pelo menos 500 caracteres de cada página.
          </small>
        )}
      </details>

      <p className={`status ${ready ? 'ready' : ''}`} role="status">
        <span aria-hidden="true" />
        {status}
      </p>

      <button
        className="analyze-button"
        type="button"
        disabled={!ready || started}
        onClick={startAnalysis}
      >
        {started ? 'Análise em andamento' : 'Iniciar análise'}
      </button>

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
                  {runState === 'failed'
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
                  : 'O processamento foi encerrado. Consulte o erro abaixo.'}
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
