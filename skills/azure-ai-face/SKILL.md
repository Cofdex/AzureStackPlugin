---
name: azure-ai-face
description: >
  Azure AI Face SDK for Python (azure-ai-vision-face). Use for face detection,
  identification (1:N), verification (1:1), finding similar faces, and liveness
  detection. Triggers on: "face detection", "FaceClient", "face recognition",
  "face identification", "verify faces", "liveness detection", "azure-ai-vision-face",
  "LargeFaceList", "LargePersonGroup". CRITICAL: Face IDs are temporary (24h TTL).
  AAD auth only works with custom subdomain endpoints. Must train groups before identify.
---

# Azure AI Face SDK for Python

## Package
```bash
uv add azure-ai-vision-face azure-identity
```

## Clients

```python
from azure.ai.vision.face import FaceClient, FaceAdministrationClient, FaceSessionClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

# Key auth (dev/test)
face_client = FaceClient(
    endpoint="https://myresource.cognitiveservices.azure.com",
    credential=AzureKeyCredential(api_key),
)

# AAD auth — ONLY works with custom subdomain, NOT regional endpoints
# e.g. https://myresource.cognitiveservices.azure.com (OK)
# e.g. https://eastus.api.cognitive.microsoft.com (NOT supported for AAD)
face_client = FaceClient(
    endpoint="https://myresource.cognitiveservices.azure.com",
    credential=DefaultAzureCredential(),
)

admin_client = FaceAdministrationClient(endpoint=..., credential=...)
session_client = FaceSessionClient(endpoint=..., credential=...)
```

## Face detection

```python
from azure.ai.vision.face.models import FaceDetectionModel, FaceRecognitionModel, FaceAttributeType

# Detect from URL
with open("photo.jpg", "rb") as f:
    img_data = f.read()

faces = face_client.detect(
    img_data,
    detection_model=FaceDetectionModel.DETECTION03,     # latest
    recognition_model=FaceRecognitionModel.RECOGNITION04,  # latest
    return_face_id=True,             # face_id valid for 24h (configurable 60-86400s)
    return_face_attributes=[
        FaceAttributeType.HEAD_POSE,
        FaceAttributeType.MASK,
        FaceAttributeType.BLUR,
    ],
    return_face_landmarks=True,
)

for face in faces:
    print(face.face_id)              # temporary ID, NOT permanent
    rect = face.face_rectangle
    print(rect.top, rect.left, rect.width, rect.height)
    attrs = face.face_attributes
    if attrs:
        print(attrs.head_pose.yaw, attrs.head_pose.pitch)
```

## Verification (1:1 — are these the same person?)

```python
result = face_client.verify_face_to_face(
    face_id1=face_id_a,
    face_id2=face_id_b,
)
print(result.is_identical)   # bool
print(result.confidence)     # 0.0–1.0
```

## Identification (1:N — who is this person?)

```python
# Step 1: Create a LargePersonGroup
admin_client.large_person_group.create(
    large_person_group_id="my-group",
    name="My Group",
    recognition_model=FaceRecognitionModel.RECOGNITION04,
)

# Step 2: Add persons
person = admin_client.large_person_group_person.create(
    large_person_group_id="my-group",
    name="Alice",
)
person_id = person.person_id

# Step 3: Add face(s) to person
with open("alice_photo.jpg", "rb") as f:
    admin_client.large_person_group_person.add_face(
        large_person_group_id="my-group",
        person_id=person_id,
        image_content=f.read(),
    )

# Step 4: Train (LRO — must wait)
poller = admin_client.large_person_group.begin_train("my-group")
poller.result()

# Step 5: Identify
results = face_client.identify_from_large_person_group(
    face_ids=[detected_face_id],
    large_person_group_id="my-group",
    confidence_threshold=0.5,
    max_num_of_candidates_returned=1,
)
for result in results:
    for candidate in result.candidates:
        print(candidate.person_id, candidate.confidence)
```

## Find similar faces

```python
similar = face_client.find_similar_from_large_face_list(
    face_id=query_face_id,
    large_face_list_id="my-list",
    max_num_of_candidates_returned=10,
)
for s in similar:
    print(s.persisted_face_id, s.confidence)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| Treating face_id as permanent | Face IDs expire after 24h (configurable, max 86400s) |
| AAD with regional endpoint `eastus.api.cognitive.microsoft.com` | AAD requires custom subdomain endpoint |
| `detect()` for liveness | Use `FaceSessionClient` — liveness is separate |
| Training group, then immediately identifying | Wait for `begin_train().result()` — LRO |
| `return_face_id=False` then trying to identify | Must set `return_face_id=True` to get IDs |
| Detection model DETECTION01 | Use DETECTION03 (latest, better accuracy) |
