import { useMemo, useState } from 'react';

type ApiResult = Record<string, unknown> | Array<unknown>;

const expectedColumns = [
  'student_name',
  'age',
  'G1',
  'G2',
  'G3',
  'absences',
  'studytime',
  'failures',
  'freetime',
  'goout',
  'Dalc',
  'Walc',
  'health',
  'traveltime',
  'famrel',
  'Medu',
  'Fedu',
  'activities',
  'internet',
  'schoolsup',
  'famsup',
  'romantic'
];

function App() {
  const apiBase = useMemo(() => (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, ''), []);
  const [file, setFile] = useState<File | null>(null);
  const [courseId, setCourseId] = useState('CURSO_ML_2026');
  const [groupSize, setGroupSize] = useState(4);
  const [sheetName, setSheetName] = useState('');
  const [result, setResult] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const templateUrl = `${apiBase}/api/v1/files/template`;

  async function callJson(path: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${apiBase}${path}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(JSON.stringify(data, null, 2));
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado');
    } finally {
      setLoading(false);
    }
  }

  async function uploadExcel(path: string) {
    if (!file) {
      setError('Primero selecciona un archivo Excel o CSV.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    if (sheetName.trim()) {
      formData.append('sheet_name', sheetName.trim());
    }

    if (path.includes('generate-groups')) {
      formData.append('course_id', courseId.trim() || 'CURSO_ML_2026');
      formData.append('group_size', String(groupSize));
    }

    try {
      const response = await fetch(`${apiBase}${path}`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(JSON.stringify(data, null, 2));
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado al procesar el archivo');
    } finally {
      setLoading(false);
    }
  }

  function handleFileChange(selected: File | null) {
    setFile(selected);
    setError(null);
    setResult(null);
  }

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">EduTech · Machine Learning</p>
          <h1>Arquitecto de Grupos de Alto Rendimiento</h1>
          <p>
            Carga un Excel con nombres de estudiantes, predice sus perfiles y genera grupos balanceados.
          </p>
        </div>

        <button className="secondary" onClick={() => callJson('/api/v1/health')}>
          Probar API
        </button>
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-header">
            <h2>Carga de Excel</h2>
            <a className="ghost link-button" href={templateUrl}>
              Descargar plantilla
            </a>
          </div>

          <label className="dropzone">
            <input
              type="file"
              accept=".xlsx,.xlsm,.csv"
              onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
            />

            <span className="drop-title">Selecciona un archivo de estudiantes</span>
            <span className="drop-subtitle">
              Formatos admitidos: .xlsx, .xlsm o .csv
            </span>

            {file && <strong className="file-name">{file.name}</strong>}
          </label>

          <div className="form-grid">
            <label>
              Curso
              <input
                value={courseId}
                onChange={(event) => setCourseId(event.target.value)}
              />
            </label>

            <label>
              Tamaño de grupo
              <input
                type="number"
                min="2"
                max="8"
                value={groupSize}
                onChange={(event) => setGroupSize(Number(event.target.value))}
              />
            </label>

            <label>
              Hoja de Excel <span className="optional">opcional</span>
              <input
                placeholder="Ejemplo: Estudiantes"
                value={sheetName}
                onChange={(event) => setSheetName(event.target.value)}
              />
            </label>
          </div>

          <div className="actions">
            <button
              onClick={() => uploadExcel('/api/v1/files/predict-profiles')}
              disabled={loading || !file}
            >
              Predecir perfiles
            </button>

            <button
              onClick={() => uploadExcel('/api/v1/files/generate-groups')}
              disabled={loading || !file}
            >
              Generar grupos
            </button>
          </div>

          <details className="columns-help">
            <summary>Columnas esperadas del Excel</summary>

            <div className="chips">
              {expectedColumns.map((column) => (
                <span key={column}>{column}</span>
              ))}
            </div>

            <p className="muted small">
              La primera columna debe ser el nombre del estudiante. También se aceptan alias como:
              nombre, alumno, estudiante, nombre completo, nombres y apellidos.
            </p>
          </details>
        </div>

        <div className="card output">
          <h2>Resultado</h2>

          {loading && <p className="muted">Procesando archivo...</p>}

          {error && <pre className="error">{error}</pre>}

          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}

          {!loading && !error && !result && (
            <p className="muted">
              Sube un Excel y ejecuta una acción para ver la respuesta.
            </p>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;