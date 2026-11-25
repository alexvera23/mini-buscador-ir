import { useEffect, useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState('Verificando...')
  const [apiMessage, setApiMessage] = useState('')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Error en la respuesta de la API')
        }
        return response.json()
      })
      .then((data) => {
        setApiStatus(data.status === 'ok' ? 'Conectado' : 'Error')
        setApiMessage(data.service)
      })
      .catch(() => {
        setApiStatus('Desconectado')
        setApiMessage('No se pudo conectar al backend')
      })
  }, [])

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <section className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">

        <header className="mb-8">
          <span className="text-sm font-semibold uppercase tracking-widest text-cyan-400">
            Recuperación de información
          </span>

          <h1 className="mt-3 text-4xl font-bold">
            Mini Buscador Web
          </h1>

          <p className="mt-3 text-slate-400">
            Proyecto de recuperación de información basado en algoritmos
            de ranking textual y estructural.
          </p>
        </header>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">
          <h2 className="text-lg font-semibold mb-4">
            Estado de los servicios
          </h2>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Backend FastAPI</span>

            <span className={`font-semibold ${
              apiStatus === 'Conectado'
                ? 'text-green-400'
                : apiStatus === 'Verificando...'
                  ? 'text-yellow-400'
                  : 'text-red-400'
            }`}>
              {apiStatus}
            </span>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            {apiMessage}
          </p>
        </div>

        <footer className="mt-8 text-sm text-slate-500">
          React · Vite · Tailwind CSS · FastAPI
        </footer>

      </section>
    </main>
  )
}

export default App