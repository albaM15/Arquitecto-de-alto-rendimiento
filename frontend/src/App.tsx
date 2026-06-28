import { useMemo, useState } from 'react';
import type { DragEvent } from 'react';

type ApiResult = Record<string, any> | Array<any>;

interface PredictionResponse {
  student_id: string;
  student_name: string;
  profile_id: number;
  profile_name: string;
  confidence: number;
  probabilities: Record<string, number>;
  model_version: string;
  explanation: string;
}

interface GroupMember {
  student_id: string;
  student_name: string;
  profile_id: number;
  profile_name: string;
  confidence: number;
  G1: number;
  risk_score: number;
}

interface GeneratedGroup {
  group_id: number;
  members: GroupMember[];
  average_G1: number;
  profile_distribution: Record<string, number>;
  explanation: string;
}

interface GroupGenerationResponse {
  course_id: string;
  group_size: number;
  generated_at: string;
  total_students: number;
  groups: GeneratedGroup[];
}

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
  const [isDragOver, setIsDragOver] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'ok' | 'failed'>('idle');

  const templateUrl = `${apiBase}/api/v1/files/template`;

  async function callJson(path: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    if (path.includes('health')) {
      setConnectionStatus('testing');
    }

    try {
      const response = await fetch(`${apiBase}${path}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(JSON.stringify(data, null, 2));
      }

      setResult(data);
      if (path.includes('health')) {
        setConnectionStatus('ok');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado');
      if (path.includes('health')) {
        setConnectionStatus('failed');
      }
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

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave() {
    setIsDragOver(false);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  }

  function handleClearFile(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setFile(null);
    setResult(null);
    setError(null);
  }

  function handleCopyJson() {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    alert('JSON copiado al portapapeles');
  }

  function handleDownloadJson() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resultado_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Type guards for results
  const isGroupResult = (res: ApiResult): res is GroupGenerationResponse => {
    return !Array.isArray(res) && 'groups' in res;
  };

  const isPredictionResult = (res: ApiResult): res is PredictionResponse[] => {
    return Array.isArray(res);
  };

  function renderError(errorStr: string) {
    try {
      const parsed = JSON.parse(errorStr);
      
      if (parsed.detail && typeof parsed.detail === 'object') {
        const detail = parsed.detail;
        const message = detail.message || 'Error de validación';
        const errorsList = Array.isArray(detail.errors) ? detail.errors : [];
        
        return (
          <div className="error-banner">
            <span className="material-symbols-outlined">error</span>
            <div className="error-content">
              <span className="error-title">{message}</span>
              {errorsList.length > 0 && (
                <ul style={{ marginTop: '8px', paddingLeft: '20px', fontSize: '13px', listStyleType: 'disc' }}>
                  {errorsList.map((err: string, i: number) => {
                    const cleanErr = err.split('\n')[0].replace(/: \d+ validation errors for StudentInput/, ': Contiene datos inválidos o incompletos');
                    return <li key={i} style={{ marginBottom: '4px' }}>{cleanErr}</li>;
                  })}
                </ul>
              )}
            </div>
          </div>
        );
      }

      if (parsed.detail && typeof parsed.detail === 'string') {
        return (
          <div className="error-banner">
            <span className="material-symbols-outlined">error</span>
            <div className="error-content">
              <span className="error-title">Error en el Servidor</span>
              <span className="error-message">{parsed.detail}</span>
            </div>
          </div>
        );
      }
    } catch (e) {
      // No es un JSON
    }

    return (
      <div className="error-banner">
        <span className="material-symbols-outlined">error</span>
        <div className="error-content">
          <span className="error-title">Error en la Solicitud</span>
          <span className="error-message">{errorStr}</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Top Navigation Bar */}
      <header className="app-header">
        <div className="header-container">
          <div className="brand">
            <span className="logo-text">EduTech</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        
        {/* Hero Section */}
        <section className="hero-section">
          <h1 className="hero-title">Forma equipos equilibrados con Machine Learning</h1>
          <p className="hero-subtitle">
            Sube tu lista de estudiantes y nuestra IA optimizará la formación de grupos basándose en perfiles académicos y sociales.
          </p>
          <div className="hero-actions">
            <a href={templateUrl} className="btn btn-outline">
              <span className="material-symbols-outlined">download</span>
              Descargar plantilla Excel
            </a>
          </div>
        </section>

        {/* Bento Grid */}
        <div className="bento-grid">
          
          {/* Card: Configuration and Upload */}
          <div className="card">
            <div className="card-title-row">
              <span className="material-symbols-outlined">upload_file</span>
              <h2 className="card-title">Configuración de Análisis</h2>
            </div>

            <div className="config-layout">
              {/* Form Fields */}
              <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Curso (Requerido)</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Ej: Matemáticas 101" 
                    value={courseId}
                    onChange={(e) => setCourseId(e.target.value)}
                  />
                </div>
                <div className="inputs-row">
                  <div className="form-group">
                    <label className="form-label">Tamaño de grupo</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      min={2} 
                      max={8} 
                      value={groupSize}
                      onChange={(e) => setGroupSize(Number(e.target.value))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Nombre de hoja</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="Opcional" 
                      value={sheetName}
                      onChange={(e) => setSheetName(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Drag and Drop Zone */}
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <label>
                  <input 
                    type="file" 
                    accept=".xlsx,.xlsm,.csv" 
                    style={{ display: 'none' }} 
                    onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                  />
                  <div 
                    className={`dropzone-container ${isDragOver ? 'dragover' : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <span className="material-symbols-outlined">cloud_upload</span>
                    <p className="dropzone-title">Arrastra tu archivo aquí</p>
                    <p className="dropzone-subtitle">o haz clic para explorar</p>
                    <div className="format-badges">
                      <span className="format-badge">.xlsx</span>
                      <span className="format-badge">.csv</span>
                    </div>
                  </div>
                </label>

                {file && (
                  <div className="selected-file-banner">
                    <div className="file-info-container">
                      <span className="material-symbols-outlined" style={{ color: 'var(--primary)' }}>description</span>
                      <span className="file-name">{file.name}</span>
                      <span style={{ color: 'var(--on-surface-variant)', fontSize: '11px' }}>
                        ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button className="btn-clear-file" onClick={handleClearFile} title="Remover archivo">
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>close</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="card-actions">
              <button 
                className="btn btn-outline"
                disabled={loading || !file}
                onClick={() => uploadExcel('/api/v1/files/predict-profiles')}
              >
                Predecir perfiles
              </button>
              <button 
                className="btn btn-primary"
                disabled={loading || !file}
                onClick={() => uploadExcel('/api/v1/files/generate-groups')}
              >
                Generar grupos
              </button>
            </div>

            {/* Expected Columns Help */}
            <details className="columns-help-details">
              <summary className="columns-help-summary">Columnas esperadas del Excel</summary>
              <div className="columns-list">
                {expectedColumns.map((col) => (
                  <span key={col} className="column-chip">{col}</span>
                ))}
              </div>
              <p className="columns-help-text">
                La primera columna debe ser el nombre del estudiante. También se aceptan alias como: 
                <em> nombre, alumno, estudiante, nombre completo, nombres y apellidos</em>.
              </p>
            </details>
          </div>
        </div>

        {/* Results / Outputs Section */}
        <section className="results-section">
          
          {/* Loading State */}
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p className="loading-title">Procesando archivo...</p>
              <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)' }}>
                Nuestra IA está analizando los perfiles estudiantiles...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && renderError(error)}

          {/* Render Predictions */}
          {result && isPredictionResult(result) && (
            <div className="profiles-output">
              <div className="results-header">
                <h3 className="results-title">Perfiles Estudiantiles Predichos</h3>
                <span style={{ fontSize: '13px', color: 'var(--on-surface-variant)', fontWeight: 600 }}>
                  Total: {result.length} estudiantes
                </span>
              </div>

              <div className="table-container">
                <table className="profiles-table">
                  <thead>
                    <tr>
                      <th>Estudiante</th>
                      <th>ID</th>
                      <th>Perfil Predicho</th>
                      <th>Confianza</th>
                      <th>Explicación</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.map((item, idx) => (
                      <tr key={item.student_id ?? idx}>
                        <td style={{ fontWeight: 600 }}>{item.student_name}</td>
                        <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{item.student_id}</td>
                        <td>
                          <span className={`badge badge-profile-${item.profile_id ?? 'default'}`}>
                            {item.profile_name}
                          </span>
                        </td>
                        <td>
                          <div className="confidence-indicator">
                            <div className="confidence-bar-bg">
                              <div 
                                className="confidence-bar-fg" 
                                style={{ width: `${item.confidence * 100}%` }}
                              ></div>
                            </div>
                            <span style={{ fontSize: '12px', fontWeight: 600 }}>
                              {(item.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td style={{ fontSize: '13px', color: 'var(--on-surface-variant)', maxWidth: '320px' }}>
                          {item.explanation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Render Groups */}
          {result && isGroupResult(result) && (
            <div className="groups-output">
              <div className="results-header">
                <h3 className="results-title">Grupos de Alto Rendimiento Generados</h3>
              </div>

              {/* Summary */}
              <div className="groups-summary-grid">
                <div className="summary-item">
                  <span className="summary-label">Curso</span>
                  <span className="summary-value" style={{ fontSize: '16px' }}>{result.course_id}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Total Estudiantes</span>
                  <span className="summary-value">{result.total_students}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Tamaño de Grupo</span>
                  <span className="summary-value">{result.group_size}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Grupos Creados</span>
                  <span className="summary-value">{result.groups.length}</span>
                </div>
              </div>

              {/* Grid of Groups */}
              <div className="groups-grid">
                {result.groups.map((group) => (
                  <div key={group.group_id} className="group-card">
                    <div className="group-card-header">
                      <span className="group-card-title">Grupo {group.group_id}</span>
                      <span className="group-average-g1">Promedio G1: {group.average_G1.toFixed(1)}</span>
                    </div>
                    <div className="group-card-body">
                      {/* Members */}
                      <div className="group-members-list">
                        {group.members.map((member) => (
                          <div key={member.student_id} className="group-member-item">
                            <div className="member-info">
                              <span className="member-name">{member.student_name}</span>
                              <span className="member-sub">Nota G1: {member.G1}</span>
                            </div>
                            <div className="member-meta">
                              <span className={`badge badge-profile-${member.profile_id ?? 'default'} member-badge`}>
                                {member.profile_name}
                              </span>
                              <span style={{ fontSize: '10px', color: 'var(--on-surface-variant)' }}>
                                Riesgo: {(member.risk_score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Profile Distribution */}
                      <div className="group-distribution">
                        <span className="distribution-title">Distribución de perfiles</span>
                        <div className="distribution-chips">
                          {Object.entries(group.profile_distribution).map(([profile, count]) => (
                            <span key={profile} className="distribution-chip">
                              {profile}: {count}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Explanation */}
                      <p className="group-explanation">{group.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}



          {/* Empty State (when no data loaded, no error, no loading) */}
          {!loading && !error && !result && (
            <div className="empty-state">
              <span className="material-symbols-outlined">analytics</span>
              <h3 className="empty-state-title">Aún no has subido ningún archivo</h3>
              <p className="empty-state-subtitle">
                Sube tu plantilla para empezar el análisis y descubrir la estructura óptima para tus equipos de trabajo.
              </p>
            </div>
          )}

        </section>
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 EduTech - Arquitecto de Grupos. Potenciado por Inteligencia Artificial y Machine Learning.</p>
      </footer>
    </>
  );
}

export default App;