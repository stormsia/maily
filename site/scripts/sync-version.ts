import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '../..');

export function syncVersion(): string {
  const pyprojectPath = path.join(rootDir, 'pyproject.toml');
  let version = '0.9.1';
  if (fs.existsSync(pyprojectPath)) {
    const content = fs.readFileSync(pyprojectPath, 'utf-8');
    const match = content.match(/version\s*=\s*"([^"]+)"/);
    if (match) {
      version = match[1].trim();
    }
  }

  // Write site/src/data/version.ts
  const versionTsPath = path.join(rootDir, 'site/src/data/version.ts');
  const tsContent = `// Auto-synced from pyproject.toml - DO NOT EDIT DIRECTLY\nexport const APP_VERSION = '${version}'; // x-release-please-version\nexport const APP_VERSION_TAG = \`v\${APP_VERSION}\`;\n`;
  fs.writeFileSync(versionTsPath, tsContent, 'utf-8');

  // Update site/package.json
  const pkgPath = path.join(rootDir, 'site/package.json');
  if (fs.existsSync(pkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    if (pkg.version !== version) {
      pkg.version = version;
      fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n', 'utf-8');
    }
  }

  // Update static templates in site/public
  const publicDir = path.join(rootDir, 'site/public');
  if (fs.existsSync(publicDir)) {
    for (const filename of ['scalar.html', 'swagger.html', 'redoc.html', 'dev/bench/index.html']) {
      const htmlFile = path.join(publicDir, filename);
      if (fs.existsSync(htmlFile)) {
        let txt = fs.readFileSync(htmlFile, 'utf-8');
        txt = txt.replace(/<span class="brand-badge">v[^<]+<\/span>/g, `<span class="brand-badge">v${version}</span>`);
        txt = txt.replace(/"softwareVersion":\s*"[^"]+"/g, `"softwareVersion": "${version}"`);
        fs.writeFileSync(htmlFile, txt, 'utf-8');
      }
    }

    for (const mdName of ['SKILL.md', 'llms-full.txt']) {
      const mdFile = path.join(publicDir, mdName);
      if (fs.existsSync(mdFile)) {
        let txt = fs.readFileSync(mdFile, 'utf-8');
        txt = txt.replace(/version:\s*[0-9.]+/gi, `version: ${version}`);
        fs.writeFileSync(mdFile, txt, 'utf-8');
      }
    }

    for (const catName of ['ard.json', '.well-known/ard.json', 'ai-catalog.json', '.well-known/ai-catalog.json']) {
      const catFile = path.join(publicDir, catName);
      if (fs.existsSync(catFile)) {
        try {
          const catData = JSON.parse(fs.readFileSync(catFile, 'utf-8'));
          catData.version = version;
          fs.writeFileSync(catFile, JSON.stringify(catData, null, 2) + '\n', 'utf-8');
        } catch {
          // ignore parsing error if any
        }
      }
    }
  }

  console.log(`[sync-version] Project version is: ${version}`);
  return version;
}

if (process.argv[1] && process.argv[1].endsWith('sync-version.ts')) {
  syncVersion();
}
