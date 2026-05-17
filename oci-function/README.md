# OCI Functions Deployment Notes

This folder contains the Function-ready code using **Resource Principal**.

## Entrypoint

- Handler: `main.handler`
- File: `src/func.py`  renamed main.py to func.py for  fn deploy

## Authentication

Uses:

```python
oci.auth.signers.get_resource_principals_signer()
```

## Return Behavior

- Returns JSON response from handler.
- HTTP `200` if no move failures.
- HTTP `207` if partially successful (`failed > 0`).
- HTTP `500` on unhandled exception.

## Required environment variables

- `SOURCE_BUCKET`
- `DEST_BUCKET`

Set the same optional variables you used in OKE (`SOURCE_PREFIX`, `DEST_ROOT_PREFIX`, `DEST_REGION`, `DELETE_SOURCE`, etc.).
