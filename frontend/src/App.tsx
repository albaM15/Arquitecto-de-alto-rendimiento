import React, { useMemo, useState } from 'react';

type ApiResult = Record<string, unknown> | Array<unknown>;

const samplePayload = {
  course_id: 'CURSO_ML_2026',
  group_size: 4,
  students: [
    { student_id: 'STU001', age: 17, G1: 16, G2: 17, G3: 18, absences: 1, studytime: 4, failures: 0, freetime: 2, goout: 2, Dalc: 1, Walc: 1, health: 5, traveltime: 1, famrel: 5, Medu: 4, Fedu: 4, activities: 'yes', internet: 'yes', schoolsup: 'no', famsup: 'yes', romantic: 'no' },
    { student_id: 'STU002', age: 18, G1: 11, G2: 12, G3: 12, absences: 6, studytime: 2, failures: 0, freetime: 4, goout: 5, Dalc: 2, Walc: 3, health: 4, traveltime: 2, famrel: 4, Medu: 3, Fedu: 2, activities: 'yes', internet: 'yes', schoolsup: 'no', famsup: 'yes', romantic: 'yes' },
    { student_id: 'STU003', age: 17, G1: 9, G2: 10, G3: 10, absences: 12, studytime: 1, failures: 1, freetime: 3, goout: 3, Dalc: 1, Walc: 2, health: 3, traveltime: 3, famrel: 3, Medu: 1, Fedu: 1, activities: 'no', internet: 'yes', schoolsup: 'yes', famsup: 'yes', romantic: 'no' },
    { student_id: 'STU004', age: 16, G1: 14, G2: 14, G3: 15, absences: 3, studytime: 3, failures: 0, freetime: 3, goout: 2, Dalc: 1, Walc: 1, health: 4, traveltime: 1, famrel: 4, Medu: 3, Fedu: 3, activities: 'yes', internet: 'yes', schoolsup: 'no', famsup: 'no', romantic: 'no' }
  ]
};

function App() {
  const apiBase = useMemo(() => (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, ''), []);
  const [payload, setPayload] = useState(JSON.stringify(samplePayload, null, 2));
  const [result, setResult] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function callApi(path: string, body?: unknown) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`${apiBase}${path}`, {
        method: body ? 'POST' : 'GET',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined
      });
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

  function parsePayload() {
    try {
      return JSON.parse(payload);
    } catch {
      throw new Error('El JSON no es válido. Revisa comas, llaves y comillas.');
    }
  }

  async function generateGroups() {
    try {
      await callApi('/api/v1/generate-groups', parsePayload());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo interpretar el JSON');
    }
  }

  async function predictFirstStudent() {
    try {
      const parsed = parsePayload();
      const firstStudent = parsed.students?.[0];
      if (!firstStudent) throw new Error('El payload debe tener students[0].');
      await callApi('/api/v1/predict-profile', { student: firstStudent });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo interpretar el JSON');
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">EduTech · Machine Learning</p>
          <h1>Arquitecto de Grupos de Alto Rendimiento</h1>
          <p>
            Clasifica estudiantes con Random Forest y forma grupos balanceados usando reglas de complementariedad.
          </p>
        </div>
        <button className="secondary" onClick={() => callApi('/health')}>Probar API</button>
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-header">
            <h2>Entrada JSON</h2>
            <button className="ghost" onClick={() => setPayload(JSON.stringify(samplePayload, null, 2))}>Cargar ejemplo</button>
          </div>
          <textarea value={payload} onChange={(event) => setPayload(event.target.value)} spellCheck={false} />
          <div className="actions">
            <button onClick={predictFirstStudent} disabled={loading}>Predecir primer estudiante</button>
            <button onClick={generateGroups} disabled={loading}>Generar grupos</button>
          </div>
        </div>

        <div className="card output">
          <h2>Resultado</h2>
          {loading && <p className="muted">Procesando...</p>}
          {error && <pre className="error">{error}</pre>}
          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
          {!loading && !error && !result && <p className="muted">Ejecuta una acción para ver la respuesta del backend.</p>}
        </div>
      </section>
    </main>
  );
}

export default App;
