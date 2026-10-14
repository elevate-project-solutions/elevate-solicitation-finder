import { afterEach, expect, test, vi } from 'vitest';
import { getHealth } from './client';

afterEach(() => {
  vi.unstubAllGlobals();
});

//uses Vitest to simulate backend responses
test('getHealth returns backend health information', async () => {
  const mockResponse = {
    status: 'healthy',
    environment: 'development',
  };

  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => mockResponse,
  });

  vi.stubGlobal('fetch', fetchMock);

  const result = await getHealth();

  expect(result).toEqual(mockResponse);
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/health'));
});

test('getHealth throws when the backend returns an error', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    }),
  );

  await expect(getHealth()).rejects.toThrow('API request failed: 500');
});
