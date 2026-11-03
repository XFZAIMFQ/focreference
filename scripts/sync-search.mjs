import { cpSync, mkdirSync } from 'node:fs';

mkdirSync('public/pagefind', { recursive: true });
cpSync('dist/pagefind', 'public/pagefind', { recursive: true, force: true });
console.log('Search index copied to public/pagefind for local development.');
