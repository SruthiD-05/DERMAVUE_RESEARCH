# DERMAVUE Design Audit and Implementation Roadmap

Audit source: safe extraction of derma-vue-dashboard-design.zip into C:\Users\fahad\AppData\Local\Temp\dermavue_ui_inspection_20260928\. Static inspection only; no install, build, render, runtime test, dependency change, or source modification was performed.

## Section 1 — Executive Summary

Subjective code-inspection completion estimate: 35–45 percent of the requested product surface, not a measured runtime metric.

Implemented well: a polished DERMAVUE landing page; responsive workspace shell; desktop sidebar and mobile drawer; top-bar search and theme toggle; dashboard; cases list; patients list; reusable shadcn-style primitives; Motion and Recharts integration; SWR hooks; IndexedDB demo/local storage; remote API abstractions; explicit demo labels and research disclaimers.

Not implemented: patient registration, clinical history form, lesion form, image upload UI, image viewer, analysis workspace, result detail, case detail, model page, about page, reports, settings, privacy controls, backend, API implementation, model adapter, checkpoint loading, and explainability display.

The route tree has only landing, dashboard, cases list, and patients list. Links to /cases/new, /cases/[id], /model, /about, and /settings have no route files.

The landing transparency section displays the hardcoded developer-reported accuracy string 94.9–95%, while correctly stating that it is unverified. This still requires source, dataset, sample size, and split context before being treated as a product claim.

## Section 2 — Project Structure

Actual structure:

    app/page.tsx
    app/layout.tsx
    app/globals.css
    app/(workspace)/layout.tsx
    app/(workspace)/dashboard/page.tsx
    app/(workspace)/cases/page.tsx
    app/(workspace)/patients/page.tsx
    components/brand
    components/cases
    components/common
    components/dashboard
    components/landing
    components/patients
    components/shell
    components/ui
    hooks/use-data.ts
    lib/config.ts
    lib/format.ts
    lib/ids.ts
    lib/types.ts
    lib/utils.ts
    lib/data/demo-seed.ts
    lib/data/local-store.ts
    lib/services/api-client.ts
    lib/services/index.ts
    public/
    package.json
    pnpm-lock.yaml
    pnpm-workspace.yaml
    next.config.mjs
    tsconfig.json
    components.json
    postcss.config.mjs

Framework: Next.js 16.3.3 App Router, React 19, TypeScript 5.7.3, Tailwind CSS 4.3.3, shadcn base-nova, Lucide, Motion 13.4.4, Recharts 3.8.0, SWR, idb-keyval, next-themes, React Hook Form/Zod dependencies. No backend files, server routes, database migrations, or API server exist.

next.config.mjs sets typescript.ignoreBuildErrors=true and images.unoptimized=true. This is a release-quality concern.

## Section 3 — Page-by-Page Audit

| Page or workflow | Status | Existing implementation | Missing elements | Relevant files |
|---|---|---|---|---|
| Shell/navigation | Partially complete | Sidebar, active indicator, mobile sheet, top search, theme toggle, model badge, skip link | Missing destination routes, profile menu, notifications, breadcrumbs, verified responsive behavior | app/(workspace)/layout.tsx, components/shell |
| Landing | Complete visually; unverified runtime | Hero, workflow, features, transparency, footer, demo assets, disclaimer | /about, /model, /cases/new targets absent; accuracy context needs review | app/page.tsx, components/landing |
| Dashboard | Partially complete | Demo/local stats, recent cases, intake chart, model status, skeletons, empty state | No real model analytics, lesion distribution, review workflow, runtime verification | components/dashboard |
| Patient registration | Missing | New-case links only | Multi-step details, consent, history, validation, review, save draft | No route/component |
| Clinical history | Missing | ClinicalHistory type only | Form and persistence UI | lib/types.ts |
| Lesion details | Missing | LesionDetails type only | Location, side, change, symptoms, notes UI | lib/types.ts |
| Image upload | Missing | CaseImage type, MIME constants, attachment service | Dropzone, picker, previews, replace/remove, progress, errors | lib/types.ts, lib/services/index.ts |
| Analysis workspace | Missing | analysisService API abstraction | Viewer, zoom/pan, modality switching, run/loading/error states | lib/services/index.ts |
| Results | Missing | AnalysisResult type and response contract | Probability view, provenance, interpretation, notes, export, unavailable state | lib/types.ts |
| Patient directory | Partially complete | Searchable table, consent/demo badges, case counts, loading/empty state | Detail view, sorting, filters, activity, mobile card view | patients-view.tsx |
| Case history | Partially complete | Search, status/review/date filters, pagination, table | Case detail, edit/delete, confirmation, result navigation | cases-view.tsx, cases-table.tsx |
| Research insights | Basic scaffold | Eight-week local case-intake chart | Lesion/age/model distributions, date controls, export, sample-size labels | activity-chart.tsx |
| Model information | Missing | ModelStatus/ModelInfo types and service calls | Page for model, checkpoint, evaluation, limitations | lib/types.ts, lib/services |
| Reports | Missing | Print fallback and remote export call abstraction | Report list, preview, actual PDF/report generation | lib/services/index.ts |
| Settings | Missing | WorkspaceSettings and local persistence | Settings route, privacy/data controls, destructive confirmations | local-store.ts |
| About/safety | Missing | Disclaimer and landing copy | /about route | app/page.tsx |

## Section 4 — Visual Quality Assessment

Branding is cohesive: navy/ivory/teal/emerald/amber palette, DERMAVUE logo, Manrope headings, Geist body, custom shadows and radii. Several strings show encoding artifacts in static source, including punctuation and ellipses.

Typography and tokenization are strong and centralized in app/globals.css. Dark-mode tokens are present. Contrast, type scale, and keyboard behavior require runtime verification.

Layout is consistent across implemented screens: 248px desktop sidebar, sticky topbar, max-width canvas, cards, tables, and responsive utility classes. Missing workflows prevent whole-product consistency assessment.

Components are reusable: PageHeader, disclaimer, status badges, case thumbnail, shell pieces, dashboard pieces, tables, and a broad UI primitive set. The main weakness is missing feature-level pages rather than absence of primitives.

Animation is partially implemented with Motion in landing reveals, hero elements, dashboard content, stat cards, and sidebar active state. CSS state animations exist in dialogs, dropdowns, selects, popovers, and tooltips. Missing: step transitions, upload feedback, image-viewer transitions, result reveals, route transitions, and real operation notifications. MotionConfig reducedMotion=user is present.

Responsiveness is code-reviewed, not runtime-verified. Mobile navigation and hidden table columns are addressed, but forms, viewers, upload layouts, charts, and result screens do not exist.

Accessibility has positive static evidence: skip link, semantic landmarks, labels, aria-current, focus-visible rings, hidden table labels, dialog titles, tooltip labels, and reduced-motion configuration. Missing/unverified: live analysis status announcements, full keyboard traversal, contrast testing, screen-reader testing, and focus behavior for future workflows.

## Section 5 — Animation Audit

| Component/page | Existing | Missing | Recommendation |
|---|---|---|---|
| Landing | Motion reveal/entrance | Runtime verification | Preserve and verify reduced motion |
| Sidebar | Motion active indicator | Collapse transition | Add only if a collapse mode is required |
| Mobile navigation | Sheet transitions | Focus and reduced-motion verification | Test focus restoration and escape |
| Dashboard | Stat and content reveals | Data-loading transition | Add restrained skeleton-to-content transition |
| Cases/patients | CSS control transitions | Filter/pagination state feedback | Add subtle, non-distracting transitions |
| New case | None, route missing | Stepper, validation, draft feedback | Add accessible step transitions |
| Upload | None, UI missing | Drag-over, preview, progress, error | Add clear state animation |
| Viewer | Missing | Zoom/pan/fullscreen transitions | Add after viewer behavior is defined |
| Results | Missing | Loading, unavailable, genuine result reveal | Animate only real returned data |
| Dialogs/popovers | CSS data-state transitions | Runtime verification | Test focus, escape, and reduced motion |
| Notifications | Toaster primitive exists | Workflow-triggered notifications | Connect to real operations |

## Section 6 — Functionality Audit

Working or meaningfully implemented in source, but not runtime verified:

- IndexedDB local persistence through lib/data/local-store.ts.
- Demo seeding with explicit origin=demo and DemoBadge rendering.
- Local/remote patient and case service abstractions.
- Case search, filters, dates, pagination, and reset behavior.
- Patient search and case-count calculation.
- Global search routing to /cases?q=...
- Mobile navigation and theme toggle.
- Model-status polling abstraction.
- Analysis POST contract for dermoscopic images.
- Local print fallback and remote report-export abstraction.

Visual-only or incomplete:

- Links to /cases/new, /cases/[id], /model, /about, and /settings have no matching page files.
- Demo result in lib/data/demo-seed.ts is explicitly source=demo and not a model prediction.
- Developer-reported accuracy is a hardcoded display string, not verified model evidence.
- analysisService.run is only a frontend API contract and sends only dermoscopic image files.
- reportService.exportPdf is only an abstraction; no report generator exists.
- No upload form exists even though image attachment types/services exist.

Missing:

- Registration wizard and forms.
- Image upload/viewer.
- Case detail/results.
- Model/about/settings/reports pages.
- Backend/model adapter/checkpoint loader.
- Explanation display.

## Section 7 — Component Inventory

Reusable shell/common: components/shell/app-sidebar.tsx, top-bar.tsx; components/common/page-header.tsx, research-disclaimer.tsx, status-badges.tsx; components/brand/logo.tsx.

Dashboard: dashboard-view.tsx, stat-cards.tsx, activity-chart.tsx, model-status-card.tsx.

Records: cases-view.tsx, cases-table.tsx, case-thumb.tsx, patients-view.tsx.

Landing: hero.tsx, workflow.tsx, features.tsx, transparency.tsx, reveal.tsx.

UI primitives: components/ui/*.tsx, including button, card, table, dialog, alert-dialog, sheet, select, tabs, tooltip, progress, skeleton, empty, forms, switches, toggles, and chart helpers.

Data/services: hooks/use-data.ts; lib/types.ts, config.ts, ids.ts, format.ts, utils.ts; lib/data/demo-seed.ts, local-store.ts; lib/services/api-client.ts and index.ts.

## Section 8 — Critical Gaps

1. Many visible navigation actions lead to routes that do not exist.
2. No patient/case creation workflow exists.
3. No upload UI or image viewer exists.
4. No analysis/result UI exists.
5. No backend, model adapter, checkpoint loading, or explanation service exists.
6. The service contract sends dermoscopic images only and does not match a clinical-plus-dermoscopic multimodal input contract.
7. The unverified 94.9–95% figure needs explicit source/evaluation context.
8. No reports, settings, model information, privacy controls, or about page exists.
9. TypeScript build errors are ignored by next.config.mjs.
10. Build, runtime, viewport, accessibility, and API behavior are unverified.

## Section 9 — Implementation Roadmap

### Phase 1 — Design Foundation

Already exists: tokens, typography, shell, logo, dark mode, common components.

Add: resolve encoding artifacts; formalize route map; add shared error/loading/not-found components; review the unverified accuracy presentation.

Likely files: app/globals.css, app/layout.tsx, lib/config.ts, components/shell, components/common, next.config.mjs.

Acceptance: all visible links resolve; type/build errors are not ignored; tokens and accessibility states are documented.

### Phase 2 — Core Patient Workflow

Already exists: domain types and local/remote case/patient services.

Add: /cases/new; multi-step patient, history, lesion, review/create workflow; React Hook Form/Zod validation; save draft; consent; error summaries.

Likely files: app/(workspace)/cases/new/page.tsx, components/cases, components/patients, lib/services/index.ts, lib/types.ts.

Acceptance: validated de-identified case creation and draft persistence.

### Phase 3 — Image Workspace

Already exists: CaseImage type, MIME constants, local attachment service.

Add: clinical/dermoscopic dropzones, previews, replacement/removal, size/type validation, dimensions, progress/errors, viewer zoom/pan/fullscreen.

Likely files: new components/images, new-case form, case detail route, services.

Prerequisite: decide whether the teammate model accepts clinical images.

Acceptance: valid uploads persist; invalid files are rejected; modalities are explicit.

### Phase 4 — Analysis and Results UI

Already exists: model status types/service, analysis API contract, disclaimers, demo-source typing.

Add: /model, /cases/[id], analysis workspace, unavailable state, genuine-result view, calibrated-score labeling, provenance, notes, errors.

Prerequisite: tested teammate model adapter, checkpoint bundle, exact input contract.

Acceptance: no prediction appears unless a backend returns it; demo outputs remain labeled.

### Phase 5 — Case Management

Already exists: tables, search, filters, pagination, local CRUD.

Add: case detail, edit/delete confirmations, review updates, patient detail, activity/history.

Acceptance: every row opens a real detail page and mutations persist safely.

### Phase 6 — Insights, Reports, and Settings

Already exists: intake chart, print/export abstraction, settings storage.

Add: explicit-data-origin insights, reports list/preview/export, settings/privacy/demo-data controls, model information, about/safety.

Acceptance: charts state sample/data origin; reports are real or clearly unavailable; destructive actions confirm.

### Phase 7 — Premium Motion and Polish

Already exists: Motion, CSS state transitions, reducedMotion=user.

Add: route/step transitions, upload feedback, viewer/result transitions, modal polish, responsive refinements, status announcements.

Acceptance: animation improves comprehension, respects reduced motion, preserves focus, and never implies model certainty.

## Section 10 — Recommended Implementation Order

1. Freeze the data/model contract and handle unverifiable performance presentation.
2. Add route skeletons and error/not-found states so current links resolve.
3. Build the new-case wizard with local validation and drafts.
4. Add image upload/storage, case detail, and viewer.
5. Test the teammate model and implement the backend/model adapter only after its exact input/checkpoint contract is known.
6. Add honest analysis unavailable states and genuine results.
7. Complete case/patient management.
8. Add model/about/settings/reports/insights.
9. Perform build, runtime, responsive, accessibility, and visual QA.
10. Add premium motion refinements last.

## Section 11 — Verification Checklist

- [ ] All visible links resolve: dashboard, cases, new case, patients, model, about, settings, and case detail.
- [ ] Landing page clearly labels demo imagery and contextualizes unverified performance.
- [ ] Desktop sidebar and mobile drawer work and restore focus.
- [ ] Global search returns correct cases.
- [ ] Registration validates and persists drafts.
- [ ] Clinical and dermoscopic uploads validate type/size and show previews.
- [ ] Images can be replaced and removed.
- [ ] Viewer supports modality switching, zoom/pan, fullscreen, and keyboard access.
- [ ] Analysis unavailable state appears when backend/checkpoint is unavailable.
- [ ] Only genuine backend results are rendered as model outputs.
- [ ] Demo results remain visibly marked.
- [ ] Results expose model version, inputs, calibration status, and disclaimer.
- [ ] Case/patient search, filters, pagination, edit, delete, and confirmations work.
- [ ] Reports are genuinely exported or clearly unavailable.
- [ ] Charts identify data origin, sample size, and date range.
- [ ] Settings/privacy/demo-data controls work.
- [ ] Desktop, laptop, tablet, and mobile layouts are rendered and reviewed.
- [ ] Keyboard, focus, labels, dialog semantics, and screen-reader status updates are reviewed.
- [ ] Reduced-motion behavior is reviewed.
- [ ] Type checking and production build are run only after reviewing ignoreBuildErrors.
- [ ] No UI claim implies clinical validation or confirmed diagnosis.
