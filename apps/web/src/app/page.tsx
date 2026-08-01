'use client';

import { ChangeEvent, useMemo, useState } from 'react';

type UploadState = {
  references: File[];
  manuscript: File | null;
};

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

  const ready = uploads.references.length >= 3 && uploads.manuscript !== null;
  const status = useMemo(() => {
    if (ready) {
      return started
        ? 'Análise iniciada. Identificando a revista e preparando o perfil editorial.'
        : 'Arquivos prontos para análise.';
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
  }, [ready, started, uploads]);

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
      <header className="brand" aria-label="Journal Matcher">
        <span className="brand-mark" aria-hidden="true">JM</span>
        <span>Journal Matcher</span>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">Prepare seu artigo para a revista certa</p>
          <h1 id="page-title">Do rascunho à submissão.</h1>
        <p className="lede">
          Envie artigos publicados na revista desejada e o seu manuscrito. O
          Journal Matcher identifica a revista, aprende seu padrão editorial e
          entrega uma revisão de forma e conteúdo.
        </p>
      </section>

      <section className="upload-panel" aria-label="Envio dos documentos">
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

      <p className={`status ${ready ? 'ready' : ''}`} role="status">
        <span aria-hidden="true" />
        {status}
      </p>

      <button
        className="analyze-button"
        type="button"
        disabled={!ready || started}
        onClick={() => setStarted(true)}
      >
        {started ? 'Análise em andamento' : 'Iniciar análise'}
      </button>

      <section className={`results ${started ? 'visible' : ''}`} aria-labelledby="results-title">
        <div>
          <p className="eyebrow">Saídas</p>
          <h2 id="results-title">Resultados</h2>
        </div>
        <p>
          Quando a análise terminar, o relatório de adequação e o artigo
          revisado aparecerão aqui para download em Word e PDF.
        </p>
        <div className="result-grid" aria-hidden={!started}>
          <article>
            <span>Relatório de adequação</span>
            <small>PDF + Word</small>
          </article>
          <article>
            <span>Artigo revisado</span>
            <small>PDF + Word</small>
          </article>
        </div>
      </section>

      <footer>
        Seus arquivos serão privados e usados somente para preparar esta revisão.
      </footer>
    </main>
  );
}
