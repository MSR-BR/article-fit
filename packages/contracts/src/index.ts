import { z } from 'zod';

export const opaqueIdSchema = z.uuid();

export const serviceNameSchema = z.enum(['web', 'api', 'worker']);

export const healthResponseSchema = z.object({
  service: serviceNameSchema,
  status: z.literal('ok'),
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
});

export const jobStateSchema = z.enum([
  'queued',
  'running',
  'succeeded',
  'failed',
  'cancelled',
]);

export const documentSlotSchema = z.enum([
  'manuscript',
  'reference-1',
  'reference-2',
  'reference-3',
]);

export const ingestionJobSchema = z.object({
  id: opaqueIdSchema,
  projectId: opaqueIdSchema,
  state: jobStateSchema,
  stage: z.string().min(1),
  progress: z.number().int().min(0).max(100),
  errorCode: z.string().nullable(),
  retryEligible: z.boolean(),
  updatedAt: z.iso.datetime({ offset: true }),
});

export const projectFoundationSchema = z.object({
  id: opaqueIdSchema,
  journalCandidate: z.string().min(2),
  journal: z
    .object({
      title: z.string().min(2),
      issn: z.string().regex(/^\d{4}-\d{3}[\dX]$/),
      officialDomain: z.string().min(3),
    })
    .nullable(),
  requiredSlots: z.array(documentSlotSchema).length(4),
  readyForResearch: z.boolean(),
  createdAt: z.iso.datetime({ offset: true }),
});

export const errorResponseSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
  correlationId: opaqueIdSchema,
  details: z.record(z.string(), z.unknown()).optional(),
});

export const sourceEvidenceSchema = z.object({
  sourceId: opaqueIdSchema,
  canonicalUrl: z.url().nullable(),
  sourceType: z.enum([
    'official-journal-page',
    'article',
    'registry',
    'repository',
  ]),
  retrievedAt: z.iso.datetime({ offset: true }),
  contentHash: z.string().regex(/^sha256:[a-f0-9]{64}$/),
  locator: z.string().min(1),
  accessStatus: z.enum(['open', 'private-derived']),
});

export const profileClaimSchema = z.object({
  key: z.string().min(1),
  claimClass: z.enum([
    'verified fact',
    'observed pattern',
    'inference',
    'expert suggestion',
  ]),
  summary: z.string().min(1),
  sourceIds: z.array(z.string().min(1)).min(1),
  locator: z.string().min(1),
  coverage: z.string().min(1),
  confidence: z.number().min(0).max(1),
});

export const researchResultSchema = z.object({
  status: z.enum(['complete', 'degraded']),
  selectedArticles: z.array(
    z.object({
      title: z.string().min(1),
      doi: z.string().nullable(),
      publishedAt: z.iso.date(),
      openUrl: z.url().nullable(),
    }),
  ),
  sources: z.array(sourceEvidenceSchema),
  limitations: z.array(z.string()),
  profilePreview: z.array(profileClaimSchema),
  profileVersion: z.unknown().nullable(),
});

export const recommendationSchema = z.object({
  id: z.string().min(1),
  key: z.string().min(1),
  anchor: z.string().min(1),
  originalText: z.string(),
  proposedText: z.string().nullable(),
  category: z.enum([
    'language',
    'structure',
    'journal-format',
    'methodology-reporting',
    'scientific-concern',
    'unresolved',
  ]),
  severity: z.enum([
    'required',
    'strongly-recommended',
    'optional',
    'question',
  ]),
  rationale: z.string().min(1),
  basis: z.enum([
    'official-requirement',
    'observed-pattern',
    'expert-suggestion',
  ]),
  sourceIds: z.array(z.string()),
  evidenceCoverage: z.string(),
  confidence: z.number().min(0).max(1),
  uncertainty: z.string(),
  scientificImpact: z.boolean(),
  decision: z.enum(['pending', 'accepted', 'rejected', 'modified']),
  modifiedText: z.string().nullable().optional(),
});

export const analysisResultSchema = z.object({
  id: z.string().min(1),
  projectId: opaqueIdSchema,
  profileVersionId: z.string().min(1),
  status: z.literal('review'),
  limitations: z.array(z.string()),
  rules: z.array(z.record(z.string(), z.unknown())),
  recommendations: z.array(recommendationSchema),
  artifacts: z.array(z.record(z.string(), z.unknown())),
  createdAt: z.iso.datetime({ offset: true }),
});

export const artifactSchema = z.object({
  artifactId: opaqueIdSchema,
  kind: z.enum([
    'revised-docx',
    'revised-pdf',
    'revision-report',
    'provenance-manifest',
  ]),
  state: z.enum(['pending', 'valid', 'invalid']),
  contentHash: z
    .string()
    .regex(/^sha256:[a-f0-9]{64}$/)
    .optional(),
});

export type HealthResponse = z.infer<typeof healthResponseSchema>;
export type JobState = z.infer<typeof jobStateSchema>;
export type DocumentSlot = z.infer<typeof documentSlotSchema>;
export type IngestionJob = z.infer<typeof ingestionJobSchema>;
export type ErrorResponse = z.infer<typeof errorResponseSchema>;
export type SourceEvidence = z.infer<typeof sourceEvidenceSchema>;
export type ProfileClaim = z.infer<typeof profileClaimSchema>;
export type ResearchResult = z.infer<typeof researchResultSchema>;
export type Recommendation = z.infer<typeof recommendationSchema>;
export type AnalysisResult = z.infer<typeof analysisResultSchema>;
export type Artifact = z.infer<typeof artifactSchema>;
