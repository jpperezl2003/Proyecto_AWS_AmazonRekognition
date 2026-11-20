import { useEffect, useRef, useState } from "react";
import "./styles.css";

const MAX_FILE_SIZE = 4 * 1024 * 1024;
const allowedTypes = ["image/jpeg", "image/png"];

const ANIMALS = {
  butterfly: { name: "Mariposa", emoji: "🦋" },
  cat: { name: "Gato", emoji: "🐱" },
  chicken: { name: "Gallina", emoji: "🐔" },
  cow: { name: "Vaca", emoji: "🐄" },
  dog: { name: "Perro", emoji: "🐕" },
  elephant: { name: "Elefante", emoji: "🐘" },
  horse: { name: "Caballo", emoji: "🐎" },
  sheep: { name: "Oveja", emoji: "🐑" },
  spider: { name: "Araña", emoji: "🕷️" },
  squirrel: { name: "Ardilla", emoji: "🐿️" },
};

const percentFormatter = new Intl.NumberFormat("es-MX", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function Icon({ name, size = 22, className = "" }) {
  const paths = {
    sparkles: (
      <>
        <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
        <path d="m19 17 .7 2.3L22 20l-2.3.7L19 23l-.7-2.3L16 20l2.3-.7L19 17Z" />
        <path d="m4 1 .7 1.8L6.5 3.5l-1.8.7L4 6l-.7-1.8-1.8-.7 1.8-.7L4 1Z" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
      </>
    ),
    arrow: (
      <>
        <path d="M4 12h15" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),
    scan: (
      <>
        <path d="M8 3H5a2 2 0 0 0-2 2v3" />
        <path d="M16 3h3a2 2 0 0 1 2 2v3" />
        <path d="M21 16v3a2 2 0 0 1-2 2h-3" />
        <path d="M8 21H5a2 2 0 0 1-2-2v-3" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    x: (
      <>
        <path d="M5 5 19 19" />
        <path d="M19 5 5 19" />
      </>
    ),
    image: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="m21 15-5-5L5 21" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
  };

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] ?? paths.sparkles}
    </svg>
  );
}

function App() {
  const inputRef = useRef(null);
  const errorRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/health", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("La API no responde");
        return response.json();
      })
      .then((data) => setApiStatus(data.status === "ok" ? "online" : "offline"))
      .catch((err) => {
        if (err.name !== "AbortError") setApiStatus("offline");
      });

    return () => controller.abort();
  }, []);

  function chooseFile(file) {
    if (loading || !file) return;
    setPrediction(null);
    setError("");
    setSelectedFile(null);
    setPreviewUrl("");

    if (!allowedTypes.includes(file.type)) {
      setError("Selecciona una fotografía JPG o PNG.");
      return;
    }
    if (file.size === 0 || file.size >= MAX_FILE_SIZE) {
      setError("Selecciona una imagen de menos de 4 MB.");
      return;
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (!loading) chooseFile(event.dataTransfer.files[0]);
  }

  function changeMode(isDemo) {
    if (loading) return;
    setDemoMode(isDemo);
    setPrediction(null);
    setError("");
  }

  async function classifyImage() {
    if (!selectedFile || loading) return;

    setError("");
    setPrediction(null);
    setLoading(true);

    try {
      if (demoMode) {
        // Resultado FIJO para probar el diseño; no analiza la imagen ni llama a AWS.
        await new Promise((resolve) => setTimeout(resolve, 700));
        setPrediction({ animal: "elephant", confidence: 99.94, simulated: true });
        return;
      }

      const formData = new FormData();
      formData.append("file", selectedFile);
      const response = await fetch("/predict", { method: "POST", body: formData });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        if (response.status === 502) {
          throw new Error("AWS no pudo procesar la imagen. Revisa si el modelo de Rekognition está iniciado y los permisos configurados.");
        }
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "No se pudo procesar la imagen. Comprueba la conexión con FastAPI."
        );
      }

      const animal = data?.prediction?.animal;
      const confidence = Number(data?.prediction?.confidence);
      if (!animal) {
        throw new Error("El modelo no identificó un animal con suficiente confianza. Prueba con otra fotografía.");
      }
      if (!Number.isFinite(confidence) || confidence < 0 || confidence > 100) {
        throw new Error("La API devolvió una confianza no válida.");
      }

      setPrediction({ animal: String(animal), confidence, simulated: false });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible realizar la clasificación.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setLoading(false);
    }
  }

  const animal = prediction
    ? ANIMALS[prediction.animal.toLowerCase()] ?? { name: prediction.animal, emoji: "🐾" }
    : null;

  return (
    <>
      <a className="skip-link" href="#contenido">Saltar al contenido</a>

      <header className="site-header" id="inicio">
        <div className="shell header-inner">
          <a className="brand" href="#inicio" aria-label="Animal Vision, volver al inicio">
            <span className="brand-mark"><Icon name="scan" size={25} /></span>
            <span className="brand-copy"><strong>animal<span>vision</span></strong><small>INTELLIGENT IMAGE LAB</small></span>
          </a>
          <nav className="header-nav" aria-label="Navegación principal">
            <a href="#como-funciona">Cómo funciona</a>
            <a className="nav-action" href="#analizador">Probar ahora <Icon name="arrow" size={16} /></a>
          </nav>
        </div>
      </header>

      <main id="contenido">
        <section className="hero shell" aria-labelledby="hero-title">
          <div className="hero-content">
            <span className="eyebrow"><span className="eyebrow-dot" /> INTELIGENCIA ARTIFICIAL APLICADA</span>
            <h1 id="hero-title">Una nueva forma de <em>ver</em> la naturaleza.</h1>
            <p>Sube una fotografía y descubre qué animal identifica nuestro modelo de Machine Learning, entrenado con Amazon Rekognition.</p>
            <a className="hero-link" href="#analizador">Explorar el clasificador <Icon name="arrow" size={18} /></a>
            <div className="hero-meta">
              <span><strong>10</strong> categorías</span>
              <span className="meta-divider" />
              <span><strong>AWS</strong> Rekognition Custom Labels</span>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="orb orb-outer" />
            <div className="orb orb-inner" />
            <div className="viewfinder">
              <span className="viewfinder-label">VISUAL ID · 01</span>
              <span className="viewfinder-center"><Icon name="scan" size={54} /></span>
              <span className="viewfinder-bottom">OBSERVAR · DETECTAR · DESCUBRIR</span>
            </div>
            <span className="orbit-animal orbit-cat">🐈</span>
            <span className="orbit-animal orbit-butterfly">🦋</span>
            <span className="orbit-animal orbit-elephant">🐘</span>
            <span className="hero-caption">POWERED BY MACHINE LEARNING <span>✦</span></span>
          </div>
        </section>

        <section className="workspace shell" id="analizador" aria-labelledby="workspace-title">
          <div className="section-heading">
            <div>
              <span className="section-kicker">EL LABORATORIO / 01</span>
              <h2 id="workspace-title">Pon a prueba la visión artificial.</h2>
              <p>Una imagen es suficiente para comenzar.</p>
            </div>
            <div className="api-indicator" aria-live="polite">
              <span className={`status-dot ${apiStatus}`} />
              {apiStatus === "online" ? "API disponible" : apiStatus === "offline" ? "API no disponible" : "Comprobando API…"}
              <span className="api-note">(no indica el estado de AWS)</span>
            </div>
          </div>

          <div className="mode-row">
            <div className="mode-tabs" role="group" aria-label="Tipo de predicción">
              <button type="button" className={!demoMode ? "active" : ""} aria-pressed={!demoMode} disabled={loading} onClick={() => changeMode(false)}>Predicción real</button>
              <button type="button" className={demoMode ? "active" : ""} aria-pressed={demoMode} disabled={loading} onClick={() => changeMode(true)}>Demo sin AWS</button>
            </div>
            <p className="mode-hint">{demoMode ? "Vista de prueba: muestra siempre un elefante simulado; no analiza la foto ni genera cargos en AWS." : "Usa el modelo de Rekognition en ejecución. Puede generar cargos por inferencia."}</p>
          </div>

          <div className="workspace-grid">
            <section className="panel upload-panel" aria-labelledby="upload-heading">
              <div className="panel-heading">
                <span className="panel-number">01</span>
                <div><h3 id="upload-heading">Tu fotografía</h3><p>Elige qué quieres descubrir.</p></div>
              </div>

              <label
                className={`dropzone ${dragging ? "dragging" : ""} ${selectedFile ? "has-file" : ""}`}
                onDragOver={(event) => { event.preventDefault(); if (!loading) setDragging(true); }}
                onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }}
                onDrop={handleDrop}
              >
                <input
                  ref={inputRef}
                  type="file"
                  name="animal-image"
                  accept="image/jpeg,image/png"
                  disabled={loading}
                  aria-label="Seleccionar una fotografía JPG o PNG"
                  onChange={(event) => { chooseFile(event.target.files?.[0]); event.target.value = ""; }}
                />
                <span className="dropzone-icon"><Icon name="upload" size={30} /></span>
                <strong>{selectedFile ? "Cambiar fotografía" : "Arrastra tu imagen aquí"}</strong>
                <span>{selectedFile ? "O selecciona otra imagen" : "O haz clic para explorar tus archivos"}</span>
                <span className="file-rules">JPG o PNG <span>·</span> Menos de 4 MB</span>
              </label>

              {previewUrl && selectedFile && (
                <div className="selected-preview">
                  <img src={previewUrl} width="800" height="520" alt="Vista previa de la fotografía seleccionada" />
                  <div className="preview-footer">
                    <div className="file-info"><Icon name="image" size={18} /><span title={selectedFile.name}>{selectedFile.name}</span></div>
                    <button type="button" className="remove-file" disabled={loading} onClick={() => { setSelectedFile(null); setPreviewUrl(""); setPrediction(null); setError(""); }} aria-label="Quitar fotografía"><Icon name="x" size={18} /></button>
                  </div>
                </div>
              )}

              <button className="classify-button" type="button" onClick={classifyImage} disabled={!selectedFile || loading}>
                {loading ? <><span className="button-spinner" aria-hidden="true" /> Analizando imagen…</> : <><Icon name="sparkles" size={20} /> {demoMode ? "Ver resultado de ejemplo" : "Identificar animal"} <Icon name="arrow" size={19} className="button-arrow" /></>}
              </button>
              <p className="upload-footnote"><Icon name="shield" size={16} /> {demoMode ? "Modo demo: no se envía ninguna fotografía." : "La fotografía se envía a tu API únicamente para clasificarla."}</p>
              {error && <p className="inline-error" ref={errorRef} tabIndex={-1} role="alert">{error}</p>}
            </section>

            <section className="panel result-panel" aria-labelledby="result-heading">
              <div className="panel-heading">
                <span className="panel-number">02</span>
                <div><h3 id="result-heading">Lo que encontramos</h3><p>Tu análisis aparecerá aquí.</p></div>
                <span className={`panel-status ${loading ? "processing" : prediction ? "done" : ""}`}>{loading ? "Analizando…" : prediction ? prediction.simulated ? "Demo" : "Completado" : "Pendiente"}</span>
              </div>

              <div className="result-body" aria-live="polite" aria-atomic="true">
                {loading ? (
                  <div className="result-empty">
                    <span className="result-empty-graphic loading-graphic"><Icon name="scan" size={46} /></span>
                    <h4>Analizando tu fotografía…</h4>
                    <p>{demoMode ? "Preparando una simulación visual." : "Esperando la respuesta de Rekognition."}</p>
                  </div>
                ) : prediction && animal ? (
                  <div className="result-complete">
                    <div className="animal-avatar" role="img" aria-label={`Animal: ${animal.name}`}>{animal.emoji}</div>
                    <span className="result-eyebrow">{prediction.simulated ? "EJEMPLO SIMULADO · NO SE ANALIZÓ LA IMAGEN" : "ESPECIE IDENTIFICADA"}</span>
                    <h4>{animal.name}</h4>
                    <p className="result-summary">{prediction.simulated ? "Este resultado es fijo para probar el diseño sin conectar con AWS." : "Esta es la categoría con mayor confianza detectada por el modelo."}</p>
                    <div className="confidence-box">
                      <div className="confidence-heading"><span>Confianza {prediction.simulated ? "de ejemplo" : "del modelo"}</span><strong>{percentFormatter.format(prediction.confidence)}%</strong></div>
                      <div className="confidence-track" role="progressbar" aria-label="Porcentaje de confianza" aria-valuemin={0} aria-valuemax={100} aria-valuenow={prediction.confidence}><div className="confidence-fill" style={{ width: `${prediction.confidence}%` }} /></div>
                      <p>{prediction.simulated ? "No es una predicción real." : "La confianza expresa la puntuación del modelo, no una garantía de acierto."}</p>
                    </div>
                    <div className="result-footer"><Icon name="check" size={17} /> {prediction.simulated ? "Modo demostración" : "Amazon Rekognition Custom Labels"}</div>
                  </div>
                ) : (
                  <div className="result-empty">
                    <span className="result-empty-graphic"><Icon name="scan" size={46} /></span>
                    <span className="empty-kicker">LISTO PARA DESCUBRIR</span>
                    <h4>La próxima pista está en tu imagen.</h4>
                    <p>Selecciona una fotografía y verás aquí el animal y su nivel de confianza.</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </section>

        <section className="how-it-works shell" id="como-funciona" aria-labelledby="steps-title">
          <div className="steps-heading"><span className="section-kicker">ASÍ DE SIMPLE / 02</span><h2 id="steps-title">De una foto a una respuesta.</h2></div>
          <div className="steps-grid">
            <div className="step"><span className="step-number">01</span><Icon name="image" size={26} /><h3>Elige una imagen</h3><p>Selecciona una fotografía JPG o PNG desde tu dispositivo.</p></div>
            <div className="step"><span className="step-number">02</span><Icon name="scan" size={26} /><h3>Analiza con IA</h3><p>FastAPI envía la imagen al modelo de Rekognition a través de Boto3.</p></div>
            <div className="step"><span className="step-number">03</span><Icon name="check" size={26} /><h3>Explora el resultado</h3><p>Consulta la categoría detectada y la confianza del modelo.</p></div>
          </div>
        </section>
      </main>

      <footer className="site-footer"><div className="shell footer-inner"><span>© Animal Vision · Proyecto de Machine Learning</span><span>React + FastAPI + AWS Rekognition</span></div></footer>
    </>
  );
}

export default App;
