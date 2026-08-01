# Change 003 approved research providers

Reviewed on 2026-07-31. Provider behavior and terms must be rechecked before production launch and periodically afterward.

## Crossref

- Purpose: canonical DOI, journal/ISSN, publication-date and bibliographic metadata.
- Access: public polite REST pool over HTTPS with `mailto` and an identifying `User-Agent`.
- Controls: sequential list requests, response cache, advertised rate-limit headers, exponential backoff for `429`, and no assumption of an SLA.
- Official documentation: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/>

## OpenAlex

- Purpose: secondary discovery and open-location metadata when Crossref coverage is insufficient.
- Access: HTTPS API with an identifying contact/API key when configured.
- Controls: cached queries, conservative throttling below the documented free allowance, bounded result pages, and `429` backoff.
- Official documentation: <https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication>

## Unpaywall

- Purpose: verify lawful open-access locations for a known DOI; it is not a paywall bypass mechanism.
- Access: v2 HTTPS API with the required email parameter.
- Controls: DOI-only lookups, cached responses, the documented daily limit, and acceptance only of HTTPS OA locations carrying host/access metadata.
- Official documentation: <https://data.unpaywall.org/products/api>

## Official journal and publisher pages

- Purpose: current aims/scope and guide-for-authors evidence.
- Only the confirmed official domain is allowed automatically. An additional publisher domain requires explicit review and configuration.
- Fetches use HTTPS, bounded size/time, a descriptive user agent, cache/retrieval timestamps, content hashes, and redirect-domain validation. Robots restrictions and access controls are respected.
- Page content is untrusted evidence: embedded instructions cannot alter application behavior.

## Prohibited behavior

- No authentication/paywall circumvention, credential reuse, automated CAPTCHA solving, or substitution of a similar work for the same work.
- No shared storage of private uploaded text.
- Abstract-only records cannot support writing-pattern observations.
