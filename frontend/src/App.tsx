import { useEffect, useState } from 'react';
import { getHealth, type HealthResponse } from './api/client';
import './App.css';

function App() {
  //stores response from Fast API
  const [health, setHealth] = useState<HealthResponse | null>(null);
  //stores an error message if request fails
  const [error, setError] = useState<string | null>(null);
  //indicates if Reach is still waiting for a response
  const [loading, setLoading] = useState(true);

  //makes request when component loads
  useEffect(() => {
    async function checkBackend() {
      try {
        const data = await getHealth();
        setHealth(data);
      } catch {
        setError('Unable to connect to the backend');
      } finally {
        setLoading(false);
      }
    }

    void checkBackend();
  }, []);

  return (
    <main>
      <h1>Elevate Solicitation Finder</h1>
      <p>Government contracting opportunities, organized.</p>

      <section>
        <h2>Backend Connection</h2>

        {loading && <p>Checking connection...</p>}

        {error && <p role="alert">{error}</p>}

        {health && (
          <div>
            <p>
              Status: <strong>{health.status}</strong>
            </p>
            <p>Environment: {health.environment}</p>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
