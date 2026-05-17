
# OCI Log Mover 

Moves log objects ( OKE Conatiner logs or any log objects)  from a source OCI Object Storage bucket path into a destination bucket path in `/YYYY/MM/DD/` structure.

This  repo has python code base and can deployed  as below 3 options :
 1. As a cronjob on Compute VM  ( Code Path :  oci-compute)
 2. As an OCI Function  ( Code Path :  oci-function)
 3. As a Cronjob / Job container with OCI Kuberenetes Engine ( OKE)

Irrespective of the approach , the code base uses Instance / Resource prinicpal 


## Example

Source object:
`<source_prefix>>/ocid1.serviceconnector.oc1.iad.../20260408T102655Z_20260408T102655Z.0.log.gz`

Destination object:
`<dest_prefix>/2026/04/08/20260408T102655Z_20260408T102655Z.0.log.gz`

## Authentication

This project uses **Instance Principal**:

- `InstancePrincipalsSecurityTokenSigner()`
- No local `~/.oci/config` needed
Ensure the node/instance running this code is in a Dynamic Group with policies that allow reading and managing object storage objects.

## Required environment variables

- `SOURCE_BUCKET`
- `DEST_BUCKET`

## Optional environment variables

- `SOURCE_PREFIX` (default: empty)
- `DEST_ROOT_PREFIX` (default: `default_ns`)
- `DEST_REGION` (recommended; if omitted, auto-detected from Object Storage endpoint)
- `DRY_RUN` (`true`/`false`, default `false`)
- `DELETE_SOURCE` (`true`/`false`, default `true`)
- `MAX_OBJECTS_PER_RUN` (default `1000`)
- `VERIFY_RETRIES` (default `20`)
- `VERIFY_DELAY_SECONDS` (default `1.0`)
- `PRESERVE_SOURCE_PREFIX` (`true`/`false`, default `true`)
- `SOURCE_KEEP_OBJECT_NAME` (default `.keep`)

## Run locally (on OCI Compute Instance with Instance Principal)

```bash
pip install -r requirements.txt
export SOURCE_BUCKET=<src>
export DEST_BUCKET=<dst>
export SOURCE_PREFIX=<src_prefix>/ocid1.serviceconnector.oc1.iad..
export DEST_REGION='us-ashburn-1'
export DEST_ROOT_PREFIX=<dest_prefix>
export DRY_RUN=false
export DELETE_SOURCE=true
export MAX_OBJECTS_PER_RUN=25
export PRESERVE_SOURCE_PREFIX=true
export SOURCE_KEEP_OBJECT_NAME=".keep"

python oci-compute/main.py
```

## OKE CronJob

Docker/Podman Build and push image to OCIR 

Use `oci-oke/cronjob.yaml` and update:

- image path
- bucket names
- source prefix
- schedule
- and other opional  parameters 

Then apply:

```bash
kubectl apply -f oci-oke/cronjob.yaml
```

 # IAM policy sketch

- `allow dynamic-group <dg-name> to read buckets in compartment <compartment-name>`
- `allow dynamic-group <dg-name> to manage objects in compartment <compartment-name>`

If source and destination buckets are in different compartments, add policy statements for both compartments.



## OCI Fn 

```bash
fn init --runtime python  log_file_mover
Copy the oci-function/log-file-mover/*  <log-file-mover-fn>
fn -v deploy --app <fn-app>
```

Set the Environment Variables OCI Console -> Developer Services -> Function -> Applications -> Configuration ( Manage Configutaion -> Add )
```
 SOURCE_BUCKET=<src>
 DEST_BUCKET=<dst>
 SOURCE_PREFIX=<src_prefix>/ocid1.serviceconnector.oc1.iad..
 DEST_REGION='us-ashburn-1'
 DEST_ROOT_PREFIX=<dest_prefix>
 DRY_RUN=false
 DELETE_SOURCE=true
 MAX_OBJECTS_PER_RUN=25
 PRESERVE_SOURCE_PREFIX=true
 SOURCE_KEEP_OBJECT_NAME=".keep"
```

 # IAM policy sketch

   Dynamic Group 
    ` ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment_ocid>'} `

   - ` allow dynamic-group <fn_dg> to read buckets in compartment <src_compartment> `
   - ` allow dynamic-group <fn_dg> to manage objects in compartment <src_compartment> `
   - ` allow dynamic-group <fn_dg> to read buckets in compartment <dst_compartment> `
   - ` allow dynamic-group <fn_dg> to manage objects in compartment <dst_compartment> `
