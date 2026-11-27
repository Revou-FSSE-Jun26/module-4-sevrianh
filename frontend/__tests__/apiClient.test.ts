import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';

const fetchMock = jest.fn();

function respond(status: number, body: unknown) {
  fetchMock.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
}

function sentHeaders(): Record<string, string> {
  return fetchMock.mock.calls[0][1].headers;
}

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  process.env.NEXT_PUBLIC_API_BASE_URL = 'http://api.test';
});

describe('apiClient', () => {
  it('unwraps data on 2xx and uses the base URL', async () => {
    respond(200, { data: { id: 'b1' } });
    await expect(apiClient.get('/api/boards/b1')).resolves.toEqual({ id: 'b1' });
    expect(fetchMock.mock.calls[0][0]).toBe('http://api.test/api/boards/b1');
  });

  it('throws ApiError with status and message on 404', async () => {
    respond(404, { error: 'x' });
    const err = await apiClient.get('/api/cards/1').catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ statusCode: 404, message: 'x' });
  });

  it('uses "Request failed" when the body has no error string', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('not json');
      },
    });
    await expect(apiClient.get('/api/x')).rejects.toMatchObject({
      statusCode: 502,
      message: 'Request failed',
    });
  });

  it('throws ApiError with statusCode 0 when fetch rejects', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('failed'));
    await expect(apiClient.get('/api/x')).rejects.toMatchObject({ statusCode: 0 });
  });

  it('sends Bearer token and JSON body on a normal request, no invite header', async () => {
    respond(201, { data: {} });
    await apiClient.post('/api/boards', { name: 'A' }, { token: 't' });
    expect(sentHeaders().Authorization).toBe('Bearer t');
    expect(sentHeaders()['X-Invite-Token']).toBeUndefined();
    expect(fetchMock.mock.calls[0][1].body).toBe('{"name":"A"}');
  });

  describe('Guest mode', () => {
    it.each(['/api/boards/b1', '/api/cards/c1/comments'])(
      'sends only X-Invite-Token on GET %s',
      async (path) => {
        respond(200, { data: {} });
        await apiClient.get(path, { inviteToken: 'inv', token: 't' });
        expect(sentHeaders()['X-Invite-Token']).toBe('inv');
        expect(sentHeaders().Authorization).toBeUndefined();
      },
    );

    it('never attaches the invite token to other requests', async () => {
      respond(200, { data: [] });
      await apiClient.get('/api/cards', { inviteToken: 'inv' });
      respond(200, { data: {} });
      await apiClient.post('/api/cards/c1/comments', { content: 'x' }, { inviteToken: 'inv' });
      respond(200, { data: {} });
      await apiClient.get('/api/boards/b1/analytics', { inviteToken: 'inv', token: 't' });
      for (const call of fetchMock.mock.calls) {
        expect(call[1].headers['X-Invite-Token']).toBeUndefined();
        expect(call[1].headers.Authorization).toBeUndefined();
      }
    });
  });
});
