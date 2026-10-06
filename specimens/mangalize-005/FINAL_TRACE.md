# MANGALIZE EVENT 005 — COMPLETE FOUNDING TRACE

EXACT PARENT
  draft PR #67
  commit: 49e9400d3753a6a308317eef8bd5b1fb93cc5322
  MANGALIZE-004 execution: c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f

SEPARATE USER SELECTION AND ADMISSION
  selected RGBA8: [0,0,0,255]
  approval SHA256: c14797ef1acd1947e525ee19ba6f7ee196edcdad388bc3c24985a9d913ff582d
  User deliberately chose this diagnostic/readable presentation witness because its observed partial-alpha absolute encoded-luma difference spans 1–89 and it produces 140 unique RGB colors. This reason is not an optimization function, universal preference, canonical background, source intent, physical print-stock claim or value judgment.

# MANGALIZE EVENT 005

SEPARATELY ADMITTED PRESENTATION
  projectionHash: adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a
  groundHash: 46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00
  proposalHash: b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041
  admissionHash: 8cc0badfb670ac12fec6cf68574a8d23353d42b8e7113b897552d5dc5944c7b0
  pagePixelMatrixHash: ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5
  pageEncodedArtifactSha256: 2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74
  presentationPixelMatrixHash: a16a6d1528b88135c5ba901da6c36e14fcff49a3250ed137899716ef607f4a9a
  presentationEncodedArtifactSha256: bb9f9e41bb8694ee71f4d9316623e6cb4879881dc590f49eacb513ceaf622fe0
  groundRGBA8: [0,0,0,255]

PARENT PAGE
  Remains exact; no replacement or source mutation.

PUBLICATION / PRINT / MOTION / SOUND / EXTERNAL GENERATION / CASTING
  Not admitted.

OUTPUT
  {"alpha": 255, "byteLength": 922098, "format": "PNG", "height": 360, "mode": "RGBA", "path": "presentation.png", "width": 640}

EXACT SEMANTICS
{
  "color": "8-bit RGBA; preserve encoded RGB channel values; no linear-light, profile or gamma conversion",
  "compositing": "Pillow Image.alpha_composite(destinationRGBA, sourceRGBA); source-over; straight 8-bit RGBA input/output; pinned imaging-binary integer arithmetic/rounding",
  "encoder": "png-rgba-unfiltered-stored/v0: PNG signature; IHDR RGBA8; one IDAT; row filter 0; zlib 0x7801 stored blocks <=65535; Adler32; IEND; CRC32; no metadata",
  "measurement": "encoded-channel luma proxy Y8=floor((2126*R+7152*G+722*B+5000)/10000); absolute Y8 difference from ground; no linearization, perceptual/physical/WCAG claim",
  "opaqueChannelArithmetic": "N=Cs*As+Cg*(255-As); Q=128*N+16384; Cout=((Q>>8)+Q)>>15; Aout=255; As=0 copies ground exactly",
  "operation": "page source-over opaque solid ground; same dimensions; straight RGBA8",
  "outputMode": "RGBA8; every output alpha byte 255",
  "pixelMatrixIdentity": "SHA256(canonical UTF-8 JSON {schema:static-collective/rgba-pixel-matrix/v0,width,height,mode:RGBA} + NUL + row-major RGBA8 bytes)",
  "quantization": "Pillow 12.1.1 AlphaComposite.c PRECISION_BITS=7 and SHIFTFORDIV255; pinned native binary",
  "transforms": {
    "blur": false,
    "colorCorrection": false,
    "crop": false,
    "gammaProfileConversion": false,
    "motion": false,
    "resize": false
  }
}

IMPLEMENTATION
{
  "implementationSha256": "f62d51f9f7e958100dd34ea729488a14566cb4be265286e2c7c7c81afa918e19",
  "rasterDependency": {
    "implementationSha256": "ae71f5c95baa2b15a92b353275af8781449713a6fdf45166a2af983231f534e6",
    "machine": "x86_64",
    "pillowImageModuleSha256": "3e5ecdcc3e8800749901e61c8108bd3c49063d3ba444fa0b62b0c18af022007f",
    "pillowImagingBinarySha256": "9b24b0f90f620e6e8882e8239081fe244cd4df8f26a5df7773049e4d87779288",
    "pillowVersion": "12.1.1",
    "pythonAbi": "cpython-312",
    "renderer": "mangalize-004/static-raster/v0",
    "system": "Linux"
  },
  "renderer": "mangalize-005/solid-ground/v0"
}

DESCRIPTIVE OBSERVATIONS
  unique RGB colors: 140
  zero-alpha parent pixels resolved onto black: 181656
  partial-alpha parent pixels composited: 10344
  opaque parent pixels: 38400
  partial-alpha absolute encoded-luma difference from black: 1–89
  all 230400 projection alpha bytes: 255
  actual matrix matches the earlier prospective matrix exactly.

COMPLETE CONTRIBUTION CUSTODY

  poster
  useHash: eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3
  assetId: page-asset:4730b32b3e6a6a201762cb0c
  admittedUseId: material-authority-use:3a859afc2ff711baa8c23910
  artifact SHA: 674a270d4a1d2aa451d713b19e4889fc2886d4a6d1961f83563f9b16007f92e7
  source-image SHA: 36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168
  003 role proposal: 4bd894362de166d468515fad4b861eb5a4e4c8eec0e063eb9370c4756c94592d
  003 placement proposal: 68429bb47600901f7ca5af3beba851637447cdb26a2e08681c491cdf3e451e5c
  003 admission: 2594deea89d7db8081515432523ccfc06746daa8e482a6a1a8f16ea1d8deae5d
  full foreign ancestry and local provenance:
{
  "admittedUseId": "material-authority-use:3a859afc2ff711baa8c23910",
  "artifact": {
    "id": "page-asset:4730b32b3e6a6a201762cb0c",
    "sha256": "674a270d4a1d2aa451d713b19e4889fc2886d4a6d1961f83563f9b16007f92e7",
    "sourceSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168"
  },
  "authority": {
    "animation": false,
    "externalGeneration": false,
    "finalPageAdmission": false,
    "publication": false,
    "render": false,
    "sound": false,
    "staging": false
  },
  "effectivePermissions": {
    "derivativeReuse": true,
    "motionAdaptation": false,
    "pixelHarvest": false,
    "pixelReuse": true,
    "publicationReuse": false,
    "synthesizedSound": false
  },
  "eventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "executionHash": "96e199c50ab4b511c48c0164c740cd2145f338847fdf77edb094468326c589ae",
      "experiment": "MANGALIZE-001",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "returnHash": "22c3368039b1e81c196f0acd9e32bfb9fb410ad364ee5c170b7fe8243f5be444",
      "verb": "MANGALIZE"
    },
    {
      "experiment": "MANGALIZE-002",
      "grantHash": "fd74e477c58228ad08adc919dc8c89123d3b1dbe2b3be82611e563b71ea40c1b",
      "grantId": "manga-quarantine-grant:fd74e477c58228ad08adc919",
      "promotionHash": "a2012b0a796061566145ffadd63fa428c4ce19a55035f2bd9bb7b0cda089be8c",
      "promotionId": "manga-quarantine-promotion:a2012b0a796061566145ffad",
      "quarantineId": "manga-quarantine-set:3581496f5329becd1a0de79b",
      "quarantineSetHash": "3581496f5329becd1a0de79b1cbe1d8191f5efa00ef30f7ac23e37076109d0cd",
      "selectionHash": "a43dc069178e0ad83422bdc5390553675777d1c9c6a56fd9b5fe7b2291074be2",
      "selectionId": "manga-quarantine-selection:a43dc069178e0ad83422bdc5",
      "verb": "MANGALIZE"
    },
    {
      "admissionHash": "2594deea89d7db8081515432523ccfc06746daa8e482a6a1a8f16ea1d8deae5d",
      "experiment": "MANGALIZE-003",
      "placementProposalHash": "68429bb47600901f7ca5af3beba851637447cdb26a2e08681c491cdf3e451e5c",
      "roleProposalHash": "4bd894362de166d468515fad4b861eb5a4e4c8eec0e063eb9370c4756c94592d",
      "verb": "MANGALIZE"
    }
  ],
  "foreignAncestry": [
    {
      "commit": "88978ff88f9b07a72040976b426b04afc2abd835",
      "handoffHash": "dd9b21083a4781e619e95a9a2f7cfdde728d570e23ea57ec22e868ab5778c42a",
      "kinds": [
        "lemonpress/manga-page/v0",
        "lemonpress/manga-performance-handoff/v0"
      ],
      "locator": {
        "editionHash": "e5e4a93558c64eb8ed89f1485e501eccdb9b201abfd5f3d9160414cd22cb6663",
        "editionId": "lemonpress:manga-press-synthetic-001:manga-001",
        "issueId": "lemonpress:manga-press-synthetic-001:issue-001",
        "pageHash": "a437492d2ac70155ae145448c442523492dc03b5f66dc401a35cb9ea52bb7dbe",
        "pageId": "page-05",
        "sourceImageSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
        "workId": "lemonpress:manga-press-synthetic-001"
      },
      "repository": "the-static-collective/lemonPRESS",
      "sourceHash": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
      "system": "lemonpress"
    }
  ],
  "originalEventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "verb": "MANGALIZE"
    }
  ],
  "schema": "haunted-blender/material-provenance/v1",
  "transformRecipe": {
    "box": [
      0,
      0,
      64,
      96
    ],
    "op": "panel-crop"
  }
}
  004 pixel lineage:
{
  "admissionHash": "1196ea5d317addd4f0c9f1c254a46de1c4312cd5550685a86e9ae7b15e48004f",
  "executionHash": "c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f",
  "experiment": "MANGALIZE-004",
  "planHash": "b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a",
  "proposalHash": "2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b",
  "verb": "MANGALIZE"
}
  005 presentation lineage:
{
  "admissionHash": "8cc0badfb670ac12fec6cf68574a8d23353d42b8e7113b897552d5dc5944c7b0",
  "groundHash": "46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00",
  "projectionHash": "adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a",
  "proposalHash": "b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041"
}

  cutaway
  useHash: ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5
  assetId: page-asset:3303923667b99a06c7417376
  admittedUseId: material-authority-use:cd1242b1e8414d215d803e7e
  artifact SHA: 0754b290a875411d4ea81e48ee433c841bd00f5627c2a1516cc24a5f24c400a8
  source-image SHA: 36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168
  003 role proposal: aa3403857025ed6fcd67cd24ee6fcf4fc2797dd53f078562a5c72ce0e7f1d24d
  003 placement proposal: 0bf04937de8b2942c93692ce5d7696dc85739c33a20e91ae63a2f5fd147f61af
  003 admission: faa2be3b4e64576938cd37ee045e3503de3a27fee6a7f268826784ba0d38082a
  full foreign ancestry and local provenance:
{
  "admittedUseId": "material-authority-use:cd1242b1e8414d215d803e7e",
  "artifact": {
    "id": "page-asset:3303923667b99a06c7417376",
    "sha256": "0754b290a875411d4ea81e48ee433c841bd00f5627c2a1516cc24a5f24c400a8",
    "sourceSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168"
  },
  "authority": {
    "animation": false,
    "externalGeneration": false,
    "finalPageAdmission": false,
    "publication": false,
    "render": false,
    "sound": false,
    "staging": false
  },
  "effectivePermissions": {
    "derivativeReuse": true,
    "motionAdaptation": false,
    "pixelHarvest": false,
    "pixelReuse": true,
    "publicationReuse": false,
    "synthesizedSound": false
  },
  "eventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "executionHash": "96e199c50ab4b511c48c0164c740cd2145f338847fdf77edb094468326c589ae",
      "experiment": "MANGALIZE-001",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "returnHash": "22c3368039b1e81c196f0acd9e32bfb9fb410ad364ee5c170b7fe8243f5be444",
      "verb": "MANGALIZE"
    },
    {
      "experiment": "MANGALIZE-002",
      "grantHash": "fd74e477c58228ad08adc919dc8c89123d3b1dbe2b3be82611e563b71ea40c1b",
      "grantId": "manga-quarantine-grant:fd74e477c58228ad08adc919",
      "promotionHash": "a2012b0a796061566145ffadd63fa428c4ce19a55035f2bd9bb7b0cda089be8c",
      "promotionId": "manga-quarantine-promotion:a2012b0a796061566145ffad",
      "quarantineId": "manga-quarantine-set:3581496f5329becd1a0de79b",
      "quarantineSetHash": "3581496f5329becd1a0de79b1cbe1d8191f5efa00ef30f7ac23e37076109d0cd",
      "selectionHash": "a43dc069178e0ad83422bdc5390553675777d1c9c6a56fd9b5fe7b2291074be2",
      "selectionId": "manga-quarantine-selection:a43dc069178e0ad83422bdc5",
      "verb": "MANGALIZE"
    },
    {
      "admissionHash": "faa2be3b4e64576938cd37ee045e3503de3a27fee6a7f268826784ba0d38082a",
      "experiment": "MANGALIZE-003",
      "placementProposalHash": "0bf04937de8b2942c93692ce5d7696dc85739c33a20e91ae63a2f5fd147f61af",
      "roleProposalHash": "aa3403857025ed6fcd67cd24ee6fcf4fc2797dd53f078562a5c72ce0e7f1d24d",
      "verb": "MANGALIZE"
    }
  ],
  "foreignAncestry": [
    {
      "commit": "88978ff88f9b07a72040976b426b04afc2abd835",
      "handoffHash": "dd9b21083a4781e619e95a9a2f7cfdde728d570e23ea57ec22e868ab5778c42a",
      "kinds": [
        "lemonpress/manga-page/v0",
        "lemonpress/manga-performance-handoff/v0"
      ],
      "locator": {
        "editionHash": "e5e4a93558c64eb8ed89f1485e501eccdb9b201abfd5f3d9160414cd22cb6663",
        "editionId": "lemonpress:manga-press-synthetic-001:manga-001",
        "issueId": "lemonpress:manga-press-synthetic-001:issue-001",
        "pageHash": "a437492d2ac70155ae145448c442523492dc03b5f66dc401a35cb9ea52bb7dbe",
        "pageId": "page-05",
        "sourceImageSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
        "workId": "lemonpress:manga-press-synthetic-001"
      },
      "repository": "the-static-collective/lemonPRESS",
      "sourceHash": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
      "system": "lemonpress"
    }
  ],
  "originalEventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "verb": "MANGALIZE"
    }
  ],
  "schema": "haunted-blender/material-provenance/v1",
  "transformRecipe": {
    "anchor": "center",
    "box": [
      12,
      18,
      52,
      78
    ],
    "op": "panel-region-crop"
  }
}
  004 pixel lineage:
{
  "admissionHash": "1196ea5d317addd4f0c9f1c254a46de1c4312cd5550685a86e9ae7b15e48004f",
  "executionHash": "c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f",
  "experiment": "MANGALIZE-004",
  "planHash": "b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a",
  "proposalHash": "2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b",
  "verb": "MANGALIZE"
}
  005 presentation lineage:
{
  "admissionHash": "8cc0badfb670ac12fec6cf68574a8d23353d42b8e7113b897552d5dc5944c7b0",
  "groundHash": "46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00",
  "projectionHash": "adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a",
  "proposalHash": "b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041"
}

  texture
  useHash: 7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde
  assetId: page-asset:a622c44b71a723710826149f
  admittedUseId: material-authority-use:beebcf6da9d2bf65fb5cf4ac
  artifact SHA: f617cc565a42f9028ac77dfc444e398ad5642d956c2a9718d8cc3c2adaad2580
  source-image SHA: 36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168
  003 role proposal: 3df4d537becdda0aa616b9343470844aab03157acd956b27eb2eebea73539cc1
  003 placement proposal: 1391368b4d35ab5244cb62fd3e36fb0d6d2ac0a55069c51010122713bea83939
  003 admission: 3e3b2d70b0a144bd2838a0ab2558c3ecd5889ba4000a2c9b4841e372bf306a76
  full foreign ancestry and local provenance:
{
  "admittedUseId": "material-authority-use:beebcf6da9d2bf65fb5cf4ac",
  "artifact": {
    "id": "page-asset:a622c44b71a723710826149f",
    "sha256": "f617cc565a42f9028ac77dfc444e398ad5642d956c2a9718d8cc3c2adaad2580",
    "sourceSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168"
  },
  "authority": {
    "animation": false,
    "externalGeneration": false,
    "finalPageAdmission": false,
    "publication": false,
    "render": false,
    "sound": false,
    "staging": false
  },
  "effectivePermissions": {
    "derivativeReuse": true,
    "motionAdaptation": false,
    "pixelHarvest": false,
    "pixelReuse": true,
    "publicationReuse": false,
    "synthesizedSound": false
  },
  "eventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "executionHash": "96e199c50ab4b511c48c0164c740cd2145f338847fdf77edb094468326c589ae",
      "experiment": "MANGALIZE-001",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "returnHash": "22c3368039b1e81c196f0acd9e32bfb9fb410ad364ee5c170b7fe8243f5be444",
      "verb": "MANGALIZE"
    },
    {
      "experiment": "MANGALIZE-002",
      "grantHash": "fd74e477c58228ad08adc919dc8c89123d3b1dbe2b3be82611e563b71ea40c1b",
      "grantId": "manga-quarantine-grant:fd74e477c58228ad08adc919",
      "promotionHash": "a2012b0a796061566145ffadd63fa428c4ce19a55035f2bd9bb7b0cda089be8c",
      "promotionId": "manga-quarantine-promotion:a2012b0a796061566145ffad",
      "quarantineId": "manga-quarantine-set:3581496f5329becd1a0de79b",
      "quarantineSetHash": "3581496f5329becd1a0de79b1cbe1d8191f5efa00ef30f7ac23e37076109d0cd",
      "selectionHash": "a43dc069178e0ad83422bdc5390553675777d1c9c6a56fd9b5fe7b2291074be2",
      "selectionId": "manga-quarantine-selection:a43dc069178e0ad83422bdc5",
      "verb": "MANGALIZE"
    },
    {
      "admissionHash": "3e3b2d70b0a144bd2838a0ab2558c3ecd5889ba4000a2c9b4841e372bf306a76",
      "experiment": "MANGALIZE-003",
      "placementProposalHash": "1391368b4d35ab5244cb62fd3e36fb0d6d2ac0a55069c51010122713bea83939",
      "roleProposalHash": "3df4d537becdda0aa616b9343470844aab03157acd956b27eb2eebea73539cc1",
      "verb": "MANGALIZE"
    }
  ],
  "foreignAncestry": [
    {
      "commit": "88978ff88f9b07a72040976b426b04afc2abd835",
      "handoffHash": "dd9b21083a4781e619e95a9a2f7cfdde728d570e23ea57ec22e868ab5778c42a",
      "kinds": [
        "lemonpress/manga-page/v0",
        "lemonpress/manga-performance-handoff/v0"
      ],
      "locator": {
        "editionHash": "e5e4a93558c64eb8ed89f1485e501eccdb9b201abfd5f3d9160414cd22cb6663",
        "editionId": "lemonpress:manga-press-synthetic-001:manga-001",
        "issueId": "lemonpress:manga-press-synthetic-001:issue-001",
        "pageHash": "a437492d2ac70155ae145448c442523492dc03b5f66dc401a35cb9ea52bb7dbe",
        "pageId": "page-05",
        "sourceImageSha256": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
        "workId": "lemonpress:manga-press-synthetic-001"
      },
      "repository": "the-static-collective/lemonPRESS",
      "sourceHash": "36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168",
      "system": "lemonpress"
    }
  ],
  "originalEventLineage": [
    {
      "admissionHash": "d904afccec60fefb88cb68f6bffb06e6ff62e01a9f34f63cd3b4182138ae2a0a",
      "requestHash": "dbf0d6385734943c81a33e57a2f8dc2c5889c1ba657ad958d44333007bf4ff9c",
      "verb": "MANGALIZE"
    }
  ],
  "schema": "haunted-blender/material-provenance/v1",
  "transformRecipe": {
    "op": "edge-mask",
    "semantic": false
  }
}
  004 pixel lineage:
{
  "admissionHash": "1196ea5d317addd4f0c9f1c254a46de1c4312cd5550685a86e9ae7b15e48004f",
  "executionHash": "c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f",
  "experiment": "MANGALIZE-004",
  "planHash": "b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a",
  "proposalHash": "2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b",
  "verb": "MANGALIZE"
}
  005 presentation lineage:
{
  "admissionHash": "8cc0badfb670ac12fec6cf68574a8d23353d42b8e7113b897552d5dc5944c7b0",
  "groundHash": "46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00",
  "projectionHash": "adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a",
  "proposalHash": "b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041"
}

UNCHANGED
  Original LemonPRESS page, closed handoff and correct 001 refusal.
  Original separate harvest-only grant, 001 request/admission/execution/return.
  Original 25-member quarantine and later three-descendant promotion.
  Remaining 22 descendants remain quarantined.
  Original 003 roles, placements, admissions, exact uses and layout.
  Original 004 plan, proposal, admission, layers, transparent PNG and pixel execution.
  All 117 historical specimen files and nine pinned implementation files.
  Original 005 candidate comparison/trace; no retroactive selection or permission.

UNADMITTED SIBLINGS
  white: proposal only; no presentation PNG/admission
  mid-gray: proposal only; no presentation PNG/admission

INDEPENDENT REPLAY
  Replays 001 → 002 → 003 → 004 before deriving 005.
  Verifies exact source bytes, raw matrix, ground/proposal scope and recorded user selection.
  Rerenders only black under the same declared implementation/native witnesses.
  Compares every persisted byte; actual observations equal the unadmitted forecast.

EFFECTIVE AUTHORITY
{
  "characterCasting": false,
  "externalGeneration": false,
  "motion": false,
  "presentation": true,
  "printAdmission": false,
  "publication": false,
  "sound": false,
  "sourceMutation": false
}

SEMANTIC NONCLAIMS
{
  "characterIdentity": null,
  "objectIdentity": null,
  "semanticIdentity": null,
  "semanticSegmentation": null,
  "sourceFact": null
}

PUBLICATION / PRINT / MOTION / SOUND
  Not admitted. No LemonPRESS state change or automatic house return.

FOUNDING LAWS
  GROUND != PAGE CONTENT
  PRESENTATION CONTEXT != SOURCE
  CANDIDATE GROUND != SELECTED GROUND
  GROUND PROPOSAL != PRESENTATION ADMISSION
  PRESENTATION != PUBLICATION
  PRESENTATION != PRINT ADMISSION
  PRESENTATION != SOURCE MUTATION
  PRESENTATION DESCENDANT != PAGE REPLACEMENT
  GROUNDING != IMAGE ENHANCEMENT
  CONTRAST MEASUREMENT != AESTHETIC JUDGMENT
  MEASUREMENT != SELECTION
  VISIBILITY != PIXEL IDENTITY
  ZERO ALPHA != ABSENT RGB
  INVISIBLE CONTRIBUTION TO PROJECTION != ABSENCE FROM PARENT
  SAME PAGE + DIFFERENT GROUND = DIFFERENT PRESENTATION
  DIFFERENT PRESENTATION != DIFFERENT SOURCE PAGE
  MULTIPLE PRESENTATIONS MAY SHARE ONE PAGE
  DISPLAY GROUND != PRINT STOCK
  SCREEN WHITE != PAPER WHITE
  SIMULATED PAPER != PHYSICAL PAPER
  ANCESTRY SURVIVES PRESENTATION
  MATERIAL != PHYSICS CLAIM
  SELECTION != UNIVERSAL PREFERENCE
  ZERO PRESENTATION CONTRAST != ABSENT PERFORMED USE
  VISIBILITY != ANCESTRY
  BLACK != BEST
  BLACK != CANONICAL BACKGROUND
  BLACK != PRINT STOCK
  BLACK != SOURCE INTENT
  HIGHER CONTRAST != HIGHER VALUE

APERTURE EXPOSED
  The first authored projection is opaque and has no optional PNG metadata.
  Pixel bytes alone do not carry its ground/page distinction or contribution custody.
  The bound transparent ancestor and receipts do. How can that context accompany
  a viewed or exchanged projection without making visibility stand in for ancestry?
