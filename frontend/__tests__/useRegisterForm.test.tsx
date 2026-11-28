import { act, renderHook } from '@testing-library/react';
import type { ChangeEvent, FormEvent } from 'react';
import { useRegisterForm, validateRegister } from '@/hooks/useRegisterForm';
import { apiClient } from '@/lib/apiClient';

const push = jest.fn();
const handleError = jest.fn();

jest.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
jest.mock('@/hooks/useErrorHandler', () => ({ useErrorHandler: () => ({ handleError }) }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { post: jest.fn() } }));

const post = apiClient.post as jest.Mock;
const submitEvent = { preventDefault: jest.fn() } as unknown as FormEvent<HTMLFormElement>;
const change = (name: string, value: string) =>
  ({ target: { name, value } }) as unknown as ChangeEvent<HTMLInputElement>;

function fillValid(result: { current: ReturnType<typeof useRegisterForm> }): void {
  act(() => result.current.handleChange(change('name', ' Alice ')));
  act(() => result.current.handleChange(change('username', 'alice_01')));
  act(() => result.current.handleChange(change('email', 'alice@example.com')));
  act(() => result.current.handleChange(change('password', 'password123')));
}

describe('validateRegister', () => {
  it('returns no errors for valid values', () => {
    const values = { name: 'A', username: 'abc', email: 'a@b.co', password: '12345678' };
    expect(validateRegister(values)).toEqual({});
  });
  it('flags every invalid field', () => {
    const errors = validateRegister({ name: ' ', username: 'a b', email: 'x', password: '123' });
    expect(Object.keys(errors).sort()).toEqual(['email', 'name', 'password', 'username']);
  });
  it('accepts the boundary lengths and rejects one past them', () => {
    const ok = {
      name: 'n'.repeat(100),
      username: 'u'.repeat(30),
      email: 'a@b.co',
      password: 'p'.repeat(128),
    };
    expect(validateRegister(ok)).toEqual({});
    const over = {
      ...ok,
      name: 'n'.repeat(101),
      username: 'u'.repeat(31),
      password: 'p'.repeat(129),
    };
    expect(Object.keys(validateRegister(over)).sort()).toEqual(['name', 'password', 'username']);
  });
});

describe('useRegisterForm', () => {
  beforeEach(() => jest.clearAllMocks());

  it('blocks submit and sends no request while a field is invalid', async () => {
    const { result } = renderHook(() => useRegisterForm());
    await act(async () => result.current.handleSubmit(submitEvent));
    expect(post).not.toHaveBeenCalled();
    expect(result.current.errors.password).toBe('Password must be 8-128 characters');
  });

  it('posts the trimmed name and redirects to /login on success', async () => {
    post.mockResolvedValue({});
    const { result } = renderHook(() => useRegisterForm());
    fillValid(result);
    await act(async () => result.current.handleSubmit(submitEvent));
    expect(post).toHaveBeenCalledWith('/api/auth/register', {
      name: 'Alice',
      username: 'alice_01',
      email: 'alice@example.com',
      password: 'password123',
    });
    expect(push).toHaveBeenCalledWith('/login');
    expect(result.current.submitting).toBe(false);
  });

  it('passes an API failure to handleError and stays on the page', async () => {
    const failure = new Error('boom');
    post.mockRejectedValue(failure);
    const { result } = renderHook(() => useRegisterForm());
    fillValid(result);
    await act(async () => result.current.handleSubmit(submitEvent));
    expect(handleError).toHaveBeenCalledWith(failure);
    expect(push).not.toHaveBeenCalled();
    expect(result.current.submitting).toBe(false);
  });
});
