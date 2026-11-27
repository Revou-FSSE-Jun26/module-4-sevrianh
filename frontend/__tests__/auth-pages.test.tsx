import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AuthProvider } from '@/context/AuthContext';
import LoginPage from '@/app/login/page';
import RegisterPage from '@/app/register/page';
import { apiClient } from '@/lib/apiClient';
import { ApiError } from '@/lib/errors';
import { showError } from '@/lib/toast';

const push = jest.fn();
jest.mock('next/navigation', () => ({ useRouter: () => ({ push, replace: jest.fn() }) }));
jest.mock('@/lib/toast', () => ({ showError: jest.fn() }));
jest.mock('@/lib/apiClient', () => ({ apiClient: { post: jest.fn() } }));

const post = apiClient.post as jest.Mock;
const user = {
  id: 'u1',
  name: 'Alice',
  username: 'alice',
  email: 'a@example.com',
  created_at: '2025-01-01T00:00:00Z',
};

function renderPage(page: React.ReactElement) {
  return render(<AuthProvider>{page}</AuthProvider>);
}
function type(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}
async function submit(name: string) {
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name }));
  });
}

beforeEach(() => jest.clearAllMocks());

describe('/register', () => {
  it('shows a validation message next to each invalid field and sends nothing', async () => {
    renderPage(<RegisterPage />);
    type('Username', 'a!');
    type('Email', 'bad');
    type('Password', 'short');
    await submit('Register');
    expect(screen.getByText('Name is required (1-100 characters)')).toBeInTheDocument();
    expect(
      screen.getByText('Username must be 3-30 letters, digits or underscores'),
    ).toBeInTheDocument();
    expect(screen.getByText('Enter a valid email')).toBeInTheDocument();
    expect(screen.getByText('Password must be 8-128 characters')).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });

  it('redirects to /login after a successful registration', async () => {
    post.mockResolvedValue(user);
    renderPage(<RegisterPage />);
    type('Name', 'Alice');
    type('Username', 'alice_01');
    type('Email', 'a@example.com');
    type('Password', 'password1');
    await submit('Register');
    await waitFor(() => expect(push).toHaveBeenCalledWith('/login'));
    expect(post).toHaveBeenCalledWith('/api/auth/register', {
      name: 'Alice',
      username: 'alice_01',
      email: 'a@example.com',
      password: 'password1',
    });
  });

  it('shows the server message as a toast on 409', async () => {
    post.mockRejectedValue(new ApiError(409, 'Email already registered'));
    renderPage(<RegisterPage />);
    type('Name', 'Alice');
    type('Username', 'alice');
    type('Email', 'a@example.com');
    type('Password', 'password1');
    await submit('Register');
    await waitFor(() => expect(showError).toHaveBeenCalledWith('Email already registered'));
    expect(push).not.toHaveBeenCalled();
  });
});

describe('/login', () => {
  it('validates email and password before sending', async () => {
    renderPage(<LoginPage />);
    type('Email', 'nope');
    await submit('Log in');
    expect(screen.getByText('Enter a valid email')).toBeInTheDocument();
    expect(screen.getByText('Password is required')).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });

  it('logs in, stores the session and redirects to /', async () => {
    post.mockResolvedValue({ access_token: 'tok', token_type: 'Bearer', expires_in: 3600, user });
    renderPage(<LoginPage />);
    type('Email', 'a@example.com');
    type('Password', 'password1');
    await submit('Log in');
    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
    expect(document.cookie).toContain('sevy_token=tok');
  });

  it('shows "Invalid credentials" inline and no session-expired toast on 401', async () => {
    post.mockRejectedValue(new ApiError(401, 'Invalid credentials'));
    renderPage(<LoginPage />);
    type('Email', 'a@example.com');
    type('Password', 'wrongpass');
    await submit('Log in');
    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(showError).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });
});
