import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { Input, Output, FileChange } from './schemas';

export class Patcher {
  async patch(input: Input): Promise<Output> {
    const startTime = Date.now();
    const changes: FileChange[] = [];

    try {
      switch (input.patchType) {
        case 'dependency-update':
          changes.push(...(await this.updateDependency(input)));
          break;
        case 'security-patch':
          changes.push(...(await this.applySecurityPatch(input)));
          break;
        case 'simple-refactor':
          changes.push(...(await this.simpleRefactor(input)));
          break;
        case 'config-update':
          changes.push(...(await this.updateConfig(input)));
          break;
      }

      const summary = this.generateSummary(changes);
      const rollbackScript = this.generateRollbackScript(changes);

      return {
        applied: !input.dryRun,
        changes,
        summary,
        patchDurationMs: Date.now() - startTime,
        rollbackScript: input.dryRun ? undefined : rollbackScript,
      };
    } catch (error: any) {
      throw new Error(`Patch failed: ${error.message}`);
    }
  }

  private async updateDependency(input: Input): Promise<FileChange[]> {
    const changes: FileChange[] = [];
    const packageJsonPath = path.join(input.repositoryPath, 'package.json');

    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }

    if (!input.changes.version) {
      throw new Error('version required for dependency-update');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    const originalContent = JSON.stringify(packageJson, null, 2);

    // Update dependency version
    let updated = false;
    if (packageJson.dependencies && packageJson.dependencies[input.target]) {
      packageJson.dependencies[input.target] = input.changes.version;
      updated = true;
    }
    if (packageJson.devDependencies && packageJson.devDependencies[input.target]) {
      packageJson.devDependencies[input.target] = input.changes.version;
      updated = true;
    }

    if (!updated) {
      throw new Error(`Dependency "${input.target}" not found in package.json`);
    }

    const newContent = JSON.stringify(packageJson, null, 2) + '\n';
    const diff = this.generateDiff(originalContent, newContent);

    if (!input.dryRun) {
      fs.writeFileSync(packageJsonPath, newContent, 'utf-8');
    }

    changes.push({
      file: packageJsonPath,
      action: 'modified',
      linesChanged: this.countLineChanges(diff),
      diff,
    });

    return changes;
  }

  private async applySecurityPatch(input: Input): Promise<FileChange[]> {
    const changes: FileChange[] = [];

    // Find target file
    const targetFile = this.findFile(input.repositoryPath, input.target);
    if (!targetFile) {
      throw new Error(`File not found: ${input.target}`);
    }

    if (!input.changes.oldValue || !input.changes.newValue) {
      throw new Error('oldValue and newValue required for security-patch');
    }

    const originalContent = fs.readFileSync(targetFile, 'utf-8');
    const newContent = originalContent.replace(
      new RegExp(input.changes.oldValue, 'g'),
      input.changes.newValue
    );

    if (originalContent === newContent) {
      throw new Error('Pattern not found in file (no changes made)');
    }

    const diff = this.generateDiff(originalContent, newContent);

    if (!input.dryRun) {
      fs.writeFileSync(targetFile, newContent, 'utf-8');
    }

    changes.push({
      file: targetFile,
      action: 'modified',
      linesChanged: this.countLineChanges(diff),
      diff,
    });

    return changes;
  }

  private async simpleRefactor(input: Input): Promise<FileChange[]> {
    const changes: FileChange[] = [];
    const files = this.getCodeFiles(input.repositoryPath);

    if (!input.changes.oldValue || !input.changes.newValue) {
      throw new Error('oldValue and newValue required for simple-refactor');
    }

    const pattern = new RegExp(input.changes.oldValue, 'g');

    for (const file of files) {
      if (input.target && !file.includes(input.target)) {
        continue; // Skip files that don't match target pattern
      }

      const originalContent = fs.readFileSync(file, 'utf-8');
      const newContent = originalContent.replace(pattern, input.changes.newValue);

      if (originalContent !== newContent) {
        const diff = this.generateDiff(originalContent, newContent);

        if (!input.dryRun) {
          fs.writeFileSync(file, newContent, 'utf-8');
        }

        changes.push({
          file,
          action: 'modified',
          linesChanged: this.countLineChanges(diff),
          diff,
        });
      }
    }

    if (changes.length === 0) {
      throw new Error('No files matched refactor pattern');
    }

    return changes;
  }

  private async updateConfig(input: Input): Promise<FileChange[]> {
    const changes: FileChange[] = [];
    const targetFile = path.join(input.repositoryPath, input.target);

    if (!input.changes.content) {
      throw new Error('content required for config-update');
    }

    const fileExists = fs.existsSync(targetFile);
    const originalContent = fileExists ? fs.readFileSync(targetFile, 'utf-8') : '';
    const newContent = input.changes.content;

    const diff = this.generateDiff(originalContent, newContent);

    if (!input.dryRun) {
      fs.writeFileSync(targetFile, newContent, 'utf-8');
    }

    changes.push({
      file: targetFile,
      action: fileExists ? 'modified' : 'created',
      linesChanged: this.countLineChanges(diff),
      diff,
    });

    return changes;
  }

  private findFile(repoPath: string, filename: string): string | null {
    const walk = (dir: string): string | null => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isFile() && entry.name === filename) {
          return fullPath;
        } else if (
          entry.isDirectory() &&
          !entry.name.startsWith('.') &&
          entry.name !== 'node_modules'
        ) {
          const found = walk(fullPath);
          if (found) return found;
        }
      }
      return null;
    };

    return walk(repoPath);
  }

  private getCodeFiles(repoPath: string): string[] {
    const files: string[] = [];
    const extensions = ['.ts', '.js', '.tsx', '.jsx', '.py', '.java', '.go'];
    const excludeDirs = ['node_modules', 'venv', '.venv', 'dist', '.git', 'build'];

    const walk = (dir: string) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!entry.name.startsWith('.') && !excludeDirs.includes(entry.name)) {
            walk(fullPath);
          }
        } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    };

    walk(repoPath);
    return files;
  }

  private generateDiff(oldContent: string, newContent: string): string {
    const oldLines = oldContent.split('\n');
    const newLines = newContent.split('\n');

    const diff: string[] = [];
    const maxLen = Math.max(oldLines.length, newLines.length);

    for (let i = 0; i < maxLen; i++) {
      if (oldLines[i] !== newLines[i]) {
        if (oldLines[i]) diff.push(`- ${oldLines[i]}`);
        if (newLines[i]) diff.push(`+ ${newLines[i]}`);
      }
    }

    return diff.join('\n');
  }

  private countLineChanges(diff: string): number {
    return diff.split('\n').filter((line) => line.startsWith('+') || line.startsWith('-'))
      .length;
  }

  private generateSummary(changes: FileChange[]): Output['summary'] {
    return {
      filesModified: changes.filter((c) => c.action === 'modified').length,
      filesCreated: changes.filter((c) => c.action === 'created').length,
      filesDeleted: changes.filter((c) => c.action === 'deleted').length,
      totalLinesChanged: changes.reduce((sum, c) => sum + (c.linesChanged || 0), 0),
    };
  }

  private generateRollbackScript(changes: FileChange[]): string {
    const commands: string[] = ['#!/bin/bash', '# Rollback script', ''];

    for (const change of changes) {
      if (change.action === 'modified') {
        commands.push(`git checkout -- "${change.file}"`);
      } else if (change.action === 'created') {
        commands.push(`rm "${change.file}"`);
      }
    }

    return commands.join('\n');
  }
}
