/* eslint-disable */
import { describe, it, expect} from 'vitest';
import { render, screen, fireEvent } from '../../tests/utils';
import { RepoSelector } from '../../components/Dashboard/RepoSelector';
import { mockRepository } from '../../tests/utils';

describe('RepoSelector', () => {
  it('renders no repositories message when empty', () => {
    render(<RepoSelector repositories={[]} />);

    expect(screen.getByText(/no active repositories/i)).toBeInTheDocument();
  });

  it('displays active repositories', () => {
    const repos = [
      mockRepository({ id: '1', name: 'Repo 1', owner: 'owner1', is_active: true }),
      mockRepository({ id: '2', name: 'Repo 2', owner: 'owner2', is_active: true }),
    ];

    render(<RepoSelector repositories={repos} />);

    expect(screen.getByText('Repo 1')).toBeInTheDocument();
    expect(screen.getByText('Repo 2')).toBeInTheDocument();
    expect(screen.getByText('owner1')).toBeInTheDocument();
    expect(screen.getByText('owner2')).toBeInTheDocument();
  });

  it('filters out inactive repositories', () => {
    const repos = [
      mockRepository({ id: '1', name: 'Active Repo', is_active: true }),
      mockRepository({ id: '2', name: 'Inactive Repo', is_active: false }),
    ];

    render(<RepoSelector repositories={repos} />);

    expect(screen.getByText('Active Repo')).toBeInTheDocument();
    expect(screen.queryByText('Inactive Repo')).not.toBeInTheDocument();
  });

  it('displays repository descriptions when available', () => {
    const repos = [
      mockRepository({
        id: '1',
        name: 'Repo 1',
        description: 'Test description',
        is_active: true,
      }),
    ];

    render(<RepoSelector repositories={repos} />);

    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('selects repository on click', () => {
    const repos = [
      mockRepository({ id: '1', name: 'Repo 1', is_active: true }),
      mockRepository({ id: '2', name: 'Repo 2', is_active: true }),
    ];

    render(<RepoSelector repositories={repos} />);

    const repo1Button = screen.getByText('Repo 1').closest('button');
    fireEvent.click(repo1Button!);

    // Check button shows selected state
    expect(repo1Button).toHaveClass('border-primary-500');
  });

  it('shows check icon on selected repository', () => {
    const repos = [
      mockRepository({ id: '1', name: 'Repo 1', is_active: true }),
    ];

    const { container } = render(<RepoSelector repositories={repos} />);

    const repoButton = screen.getByText('Repo 1').closest('button');
    fireEvent.click(repoButton!);

    // Check icon should be visible after selection
    const checkIcon = container.querySelector('svg[class*="text-primary-500"]');
    expect(checkIcon).toBeInTheDocument();
  });

  it('changes selection when different repo clicked', () => {
    const repos = [
      mockRepository({ id: '1', name: 'Repo 1', is_active: true }),
      mockRepository({ id: '2', name: 'Repo 2', is_active: true }),
    ];

    render(<RepoSelector repositories={repos} />);

    const repo1Button = screen.getByText('Repo 1').closest('button');
    const repo2Button = screen.getByText('Repo 2').closest('button');

    fireEvent.click(repo1Button!);
    expect(repo1Button).toHaveClass('border-primary-500');

    fireEvent.click(repo2Button!);
    expect(repo2Button).toHaveClass('border-primary-500');
    expect(repo1Button).not.toHaveClass('border-primary-500');
  });
});
