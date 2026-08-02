'use client';

import { ChangeEvent, useMemo, useState } from 'react';

type UploadState = {
  references: File[];
  manuscript: File | null;
};

const progressStages = [
  'Criando o projeto',
  'Enviando e validando os arquivos',
  'Pesquisando a revista e revisando o artigo',
  'Arquivos prontos',
] as const;

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
  const [error, setError] = useState('');
  const [analysisId, setAnalysisId] = useState('');
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [guidance, setGuidance] = useState({
    scopeUrl: '',
    guideUrl: '',
    scopeSnapshot: '',
    guideSnapshot: '',
  });

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
      const documents = [
        ...uploads.references
          .slice(0, 3)
          .map((file, index) => ({ file, slot: `reference-${index + 1}` })),
        { file: uploads.manuscript, slot: 'manuscript' },
      ];
      for (const { file, slot } of documents) {
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
      }
      setActiveStep(2);
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
          const job = await api<{
            state: string;
            progress: number;
            errorCode?: string | null;
          }>(`/jobs/${workflow.id}`);
          setActiveStep(job.progress >= 100 ? 3 : 2);
          if (job.state === 'failed' || job.state === 'cancelled') {
            throw new Error(
              job.errorCode
                ? `A análise falhou (${job.errorCode}).`
                : 'A análise não foi concluída.',
            );
          }
          if (job.state === 'succeeded') {
            workflow = await api<{
              analysisId: string;
              artifacts: Array<{ kind: string }>;
            }>(`/projects/${project.id}/latest-analysis`);
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
      setActiveStep(3);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Não foi possível concluir a análise.',
      );
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
                  <span className="spinner" aria-hidden="true" />
                  Preparando seu artigo
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
            <p id="progress-description" className="progress-description">
              Cada etapa é marcada somente após a confirmação do servidor.
            </p>
            <div
              className="progress-track determinate"
              role="progressbar"
              aria-label="Andamento da análise"
              aria-valuemin={0}
              aria-valuemax={progressStages.length}
              aria-valuenow={activeStep + 1}
            >
              <span
                style={{
                  width: `${((activeStep + 1) / progressStages.length) * 100}%`,
                }}
              />
            </div>
            <ol className="progress-steps">
              {progressStages.map((stage, index) => {
                const state =
                  index < activeStep
                    ? 'complete'
                    : index === activeStep
                      ? error
                        ? 'error'
                        : 'active'
                      : '';
                const label =
                  index < activeStep
                    ? 'Concluído'
                    : index === activeStep
                      ? error
                        ? 'Interrompido'
                        : 'Em andamento'
                      : 'Aguardando';
                return (
                  <li className={state} key={stage}>
                    <span
                      className={state === 'active' ? 'step-spinner' : ''}
                      aria-hidden="true"
                    />
                    <div>
                      <strong>{stage}</strong>
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
            {activeStep === progressStages.length - 1 && !error && (
              <p className="preview-notice" role="status">
                Análise concluída. Os arquivos estão disponíveis abaixo.
              </p>
            )}
            <button
              type="button"
              className="background-button"
              onClick={hideProgress}
            >
              Continuar em segundo plano
            </button>
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
