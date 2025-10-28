import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RepoSelector } from '../../components/Dashboard/RepoSelector';
import { renderWithRouter } from '../../test-utils/test-utils';
import { mockRepository } from '../../test-utils/mocks';

describe('RepoSelector', () => {
  it('displays "No active repositories" message when repositories list is empty', () => {
    renderWithRouter(<RepoSelector repositories={[]} />);

    expect(screen.getByText('No active repositories')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays "No active repositories" message when all repositories are inactive', () => {
    const inactiveRepos = [
      mockRepository({ id: '1', name: 'repo1', is_active: false }),
      mockRepository({ id: '2', name: 'repo2', is_active: false }),
    ];

    renderWithRouter(<RepoSelector repositories={inactiveRepos} />);

    expect(screen.getByText('No active repositories')).toBeInTheDocument();
  });

  it('renders active repositories in a grid', () => {
    const repos = [
      mockRepository({ id: '1', name: 'repo1', owner: 'owner1', is_active: true }),
      mockRepository({ id: '2', name: 'repo2', owner: 'owner2', is_active: true }),
      mockRepository({ id: '3', name: 'repo3', owner: 'owner3', is_active: true }),
    ];

    renderWithRouter(<RepoSelector repositories={repos} />);

    expect(screen.getByText('repo1')).toBeInTheDocument();
    expect(screen.getByText('repo2')).toBeInTheDocument();
    expect(screen.getByText('repo3')).toBeInTheDocument();
    expect(screen.getByText('owner1')).toBeInTheDocument();
    expect(screen.getByText('owner2')).toBeInTheDocument();
    expect(screen.getByText('owner3')).toBeInTheDocument();
  });

  it('filters out inactive repositories', () => {
    const repos = [
      mockRepository({ id: '1', name: 'active-repo', is_active: true }),
      mockRepository({ id: '2', name: 'inactive-repo', is_active: false }),
    ];

    renderWithRouter(<RepoSelector repositories={repos} />);

    expect(screen.getByText('active-repo')).toBeInTheDocument();
    expect(screen.queryByText('inactive-repo')).not.toBeInTheDocument();
  });

  it('displays repository description when available', () => {
    const repos = [
      mockRepository({
        id: '1',
        name: 'repo1',
        description: 'A test repository',
        is_active: true,
      }),
    ];

    renderWithRouter(<RepoSelector repositories={repos} />);

    expect(screen.getByText('A test repository')).toBeInTheDocument();
  });

  it('selects a repository when clicked', async () => {
    const user = userEvent.setup();
    const repos = [
      mockRepository({ id: '1', name: 'repo1', is_active: true }),
      mockRepository({ id: '2', name: 'repo2', is_active: true }),
    ];

    renderWithRouter(<RepoSelector repositories={repos} />);

    const repo1Button = screen.getByLabelText(/Select repository.*repo1/);
    await user.click(repo1Button);

    expect(repo1Button).toHaveAttribute('aria-pressed', 'true');
  });

  it('has proper ARIA labels for accessibility', () => {
    const repos = [
      mockRepository({
        id: '1',
        name: 'test-repo',
        full_name: 'owner/test-repo',
        description: 'Test description',
        is_active: true,
      }),
    ];

    renderWithRouter(<RepoSelector repositories={repos} />);

    expect(screen.getByRole('group', { name: 'Repository selector' })).toBeInTheDocument();
    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getByLabelText(/Select repository.*test-repo.*Test description/)).toBeInTheDocument();
  });
});
