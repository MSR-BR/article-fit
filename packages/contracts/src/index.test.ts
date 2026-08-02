import { describe, expect, it } from 'vitest';
import {
  healthResponseSchema,
  ingestionJobSchema,
  jobStateSchema,
  researchResultSchema,
  analysisResultSchema,
  sourceEvidenceSchema,
} from './index.js';

describe('base contracts', () => {
  it('accepts the versioned health response', () => {
    expect(
      healthResponseSchema.parse({
        service: 'api',
        status: 'ok',
        version: '0.1.0',
      }),
    ).toEqual({ service: 'api', status: 'ok', version: '0.1.0' });
  });

  it('rejects unknown job states', () => {
    expect(() => jobStateSchema.parse('waiting-for-magic')).toThrow();
  });

  it('requires a verifiable evidence hash', () => {
    expect(() =>
      sourceEvidenceSchema.parse({
        sourceId: '36b8f84d-df4e-4d49-b662-bcde71a8764f',
        canonicalUrl: 'https://example.org/source',
        sourceType: 'article',
        retrievedAt: '2026-07-31T12:00:00Z',
        contentHash: 'invented',
        locator: 'page 1',
        accessStatus: 'open',
      }),
    ).toThrow();
  });

  it('validates bounded ingestion progress', () => {
    expect(
      ingestionJobSchema.parse({
        id: '11111111-1111-4111-8111-111111111111',
        projectId: '22222222-2222-4222-8222-222222222222',
        state: 'succeeded',
        stage: 'ingestion-complete',
        progress: 100,
        errorCode: null,
        errorDetail: null,
        retryEligible: false,
        updatedAt: '2026-07-31T12:00:00+00:00',
      }).progress,
    ).toBe(100);
  });

  it('keeps degraded research limitations explicit', () => {
    expect(
      researchResultSchema.parse({
        status: 'degraded',
        selectedArticles: [],
        sources: [],
        limitations: ['Only 0 of 3 articles were available'],
        profilePreview: [],
        profileVersion: null,
      }).limitations,
    ).toHaveLength(1);
  });

  it('requires scientific-impact and decision fields on recommendations', () => {
    expect(() =>
      analysisResultSchema.parse({
        id: 'analysis',
        projectId: '11111111-1111-4111-8111-111111111111',
        profileVersionId: 'profile',
        status: 'review',
        limitations: [],
        rules: [],
        recommendations: [{ rationale: 'unsupported partial record' }],
        artifacts: [],
        createdAt: '2026-07-31T12:00:00+00:00',
      }),
    ).toThrow();
  });
});
