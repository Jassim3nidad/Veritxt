# Reporting readiness: all deployment gates pending

A local development prototype prepared for possible future reporting integration after approval and security controls are completed.

Android remains offline: DisabledReportingRepository, no INTERNET permission, no endpoint, uploader, HTTP client, retry queue or transmitting report button. Experimental and synthetic detections cannot form report payloads. Passing local tests does not authorize reporting.

Every gate below remains **pending**. A development bearer token does not satisfy staff authentication or authorization. Existing project/client permission to develop is not acceptance of a deployed reporting service.

- [ ] HTTPS/TLS
- [ ] Staff authentication
- [ ] Role-based authorization
- [ ] Rate limiting without persistent device tracking
- [ ] Retention and deletion policy
- [ ] Abuse handling
- [ ] Partner/client acceptance of reporting
- [ ] Security and privacy review (including infrastructure logging)
- [ ] Production WSGI hosting
- [ ] Approved endpoint ownership and configuration
- [ ] Explicit user consent flow for transmission
- [ ] Verification that reporting is optional
- [ ] Final review of transmitted metadata

Local prototype checks: six allowed keys; unknown/identifying fields rejected; 4096-byte body limit; finite bounded scores; controlled city/brand/class; conservative domains; hour-only timestamps with offsets; no IP storage column or request-body logging; demo cohorts separated from voluntary-report aggregates. This is technical preparation, not completion of the deployment gates. Null domains mean no reportable domain, not proven linklessness. Counts are submissions, not unique victims or citywide prevalence.
