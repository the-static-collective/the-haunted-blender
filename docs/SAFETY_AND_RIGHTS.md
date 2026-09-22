# Stewardship of personal archives and filmed people

This project may process intensely personal photographs and recordings. Its default is to remain entirely on the user's machine. No automatic uploads, face identification, voice cloning, biometric classification, or public export are authorized by a file import.

- An image of a person establishes the image's existence, **not** that person's identity, intentions, consent, relationship, or authorization for commercial/public use.
- Story and documentary modes must distinguish observed source evidence, user-attributed claims, interpretation, fiction, reconstruction, and unresolved uncertainty.
- AI-generated actors, movement, conversations and interviews must not be represented as historical recordings of events that never occurred.
- Copyright and permission status are associated with individual source assets and derivatives; an unassessed source must not silently become cleared for publication.
- Remote processing, public sharing and paid-model invocation require their own opt-in gates, which are not implemented in the scaffold.
- This prototype uses absolute local source paths and unencrypted SQLite metadata. Protect access to the library folder and avoid distributing it as a public dataset; an encrypted managed vault and portable project references are future work.
- Source edits, deletion, and app-directed file moves are deliberately absent from v0. Backup and restore procedures are required before production deployment.
- Do not put actual personal photographs, exported stills, location metadata, sidecars, projects or render receipts in public source control; `.gitignore` protects common extensions but is not a security mechanism.
