# FOC Reference — Bilingual (EN / ZH) Study Edition

[English](README.md) | [简体中文](README.zh-CN.md)

> [!IMPORTANT]
> **Copyright & Attribution Notice**
>
> All original text, equations, interactive simulations, diagrams, and visual design of this site originate from and are copyrighted by **[focreference.com](https://focreference.com/)**.
>
> This repository is an **unofficial bilingual (English / Simplified Chinese) translation and static rebuild created strictly for personal study, educational reference, and non-commercial learning**. It is **not** the official source repository of `focreference.com`. If you are the copyright holder and would like this repository modified or removed, please open an issue.

---

## Overview

[FOC Reference](https://focreference.com/) is an interactive technical reference on **Field-Oriented Control (FOC)** of permanent-magnet synchronous motors (PMSMs) — covering everything from rotating space vectors and Clarke/Park coordinate transforms to current/speed loop tuning, sensorless observers, and production-ready interrupt service routine (ISR) architecture.

This project provides a side-by-side bilingual static rebuild of all **29 pages** from the original site:
- **6 Chapters (24 Pages)**:
  1. **Foundations**: Space vectors, three-phase power, Clarke & Park transforms, per-unit & fixed-point scaling
  2. **The Machine**: PMSM $dq$ model, parameter identification, torque & MTPA, field weakening
  3. **The Inverter**: Three-phase bridge & losses, six-step commutation, space-vector PWM (SVPWM), deadtime & compensation
  4. **Sensing**: Shunt current measurement windows, ADC quantisation in $dq$, DC-link ripple & braking, position sensors & $d$-axis offset
  5. **Control & Estimation**: Current loop tuning & anti-windup, cascaded speed/position loops, sampled-time effects & aliasing, sensorless observers (flux linkage & SMO)
  6. **Implementation**: Timing & phase margin budget, MCU peripherals & shadow registers, software architecture, step-by-step drive bring-up
- **Home, Search & 3 Reference Pages**:
  - Interactive Hero Loop (`index.html`), Full-Text Search (`search.html`), What Goes Wrong (`failures.html`), Formula Sheet (`formulas.html`), and Notation (`notation.html`).

### Translation & Proofreading Notes

- All 29 Chinese pages (`src/docs/zh/*.html`) and their embedded SVG block diagrams have been thoroughly proofread against the original English pages (`src/docs/en/*.html`) for domain terminology in motor control and power electronics.
- All KaTeX mathematical expressions, code blocks, and interactive Canvas/SVG widgets are preserved 100% intact.
- Use the **English / 中文** button in the top navigation bar on any page to switch between languages at the same route.

---

## Local Development

Requires **Node.js 20+**.

```bash
# Install dependencies
npm install

# Start local dev server
npm run dev
```

Open `http://localhost:4321/zh/` (or `http://localhost:4321/en/`) in your browser.

### Building for Production

```bash
npm run build
npm run preview
```

`npm run build` runs `astro build` to generate static HTML in `dist/`, indexes both English and Chinese pages with **Pagefind**, and syncs the search index to `public/pagefind/` for local preview.

---

## Deployment on GitHub Pages

This repository includes an automated GitHub Actions workflow (`.github/workflows/deploy.yml`) that configures the Astro `base` path automatically (`SITE_URL` and `BASE_PATH`) so the site works seamlessly whether hosted at a root domain or a project subpath (`https://<username>.github.io/<repo>/`).

1. Push this repository to GitHub (`main` branch).
2. In your GitHub repository, navigate to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Open the **Actions** tab, select **Deploy to GitHub Pages**, and click **Run workflow** whenever you want to build and publish the site.

---

## Project Structure

- `src/docs/en/` — Original English HTML pages (29 pages).
- `src/docs/zh/` — Proofread Simplified Chinese HTML pages (29 pages).
- `src/docs/pages.json` — Route manifest mapping all 29 pages.
- `src/pages/[...route].astro` — Bilingual route generator, language switcher injection, and `BASE_URL` asset resolution.
- `src/pages/index.astro` — Root entry page redirecting to `/zh/`.
- `public/_astro/` — Compiled interactive Canvas simulation scripts, styles, and KaTeX fonts from the public site.
- `public/i18n.css` — Typography adjustments and language switcher styling.
