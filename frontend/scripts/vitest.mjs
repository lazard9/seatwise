// Runs Vitest with the drive letter of the working directory in upper case.
//
// On Windows, d:\project and D:\project are the same folder, but when the shell
// starts in d:\ (VS Code and Git Bash often do), Vitest loads a second copy of
// its own module for test files and fails with "failed to find the current
// suite". On Linux and macOS the path is passed through unchanged.
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const upperDrive = (path) => path.replace(/^[a-z]:/, (drive) => drive.toUpperCase())

const cwd = upperDrive(process.cwd())
const vitestBin = upperDrive(
  fileURLToPath(new URL('../node_modules/vitest/vitest.mjs', import.meta.url)),
)

const result = spawnSync(process.execPath, [vitestBin, ...process.argv.slice(2)], {
  cwd,
  stdio: 'inherit',
})

process.exit(result.status ?? 1)
