# MANGALIZE EVENT 005 — CANDIDATE TRACE

PRESENTATION GROUND READY — SELECTION / ADMISSION REQUIRED

EXACT PARENT
  PR #67: 49e9400d3753a6a308317eef8bd5b1fb93cc5322
  execution: c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f
  pagePixelMatrixHash: ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5
  pageEncodedArtifactSha256: 2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74
  dimensions: 640 × 360 RGBA8; parent remains transparent and byte-identical

UNSELECTED CANDIDATES
  White and black are encoded-channel endpoint probes.
  Mid-gray 128 is the positive-half-up midpoint of encoded 0..255, not linear-light gray.
  Names and listing order confer no preference, print stock or selected ground.

  white
  rgba8: [255, 255, 255, 255]
  groundHash: 1172efe2796c898630568fd693d14bb74bfae009c7c2490082bc6f9608cd0a7a
  proposalHash: 5078fa302c3205206e72c75cd8cbcb7bd5437b084b969707f3bfa78b98ee63c3
  prospective matrix: 7a048c1fc67ff46f6ede1472c7965766ff783758dce6ad33b7c771b38b302529
  unique RGB colors: 92
  encoded luma range: [127, 255]
  transparency: {'zeroAlphaParentPixelsReceiveGround': 181656, 'partialAlphaParentPixelsComposited': 10344, 'opaqueParentPixels': 38400, 'hiddenNonzeroRGBAtParentAlphaZero': 0, 'partialAlphaResultRGBChangedFromSource': 0, 'nonzeroAlphaPixelsMatchingGroundRGB': 17320}
  partial-alpha |luma-ground| histogram: {0: 10344}

  black
  rgba8: [0, 0, 0, 255]
  groundHash: 46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00
  proposalHash: b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041
  prospective matrix: a16a6d1528b88135c5ba901da6c36e14fcff49a3250ed137899716ef607f4a9a
  unique RGB colors: 140
  encoded luma range: [0, 255]
  transparency: {'zeroAlphaParentPixelsReceiveGround': 181656, 'partialAlphaParentPixelsComposited': 10344, 'opaqueParentPixels': 38400, 'hiddenNonzeroRGBAtParentAlphaZero': 0, 'partialAlphaResultRGBChangedFromSource': 10344, 'nonzeroAlphaPixelsMatchingGroundRGB': 0}
  partial-alpha |luma-ground| histogram: {1: 1628, 2: 92, 3: 1488, 4: 76, 5: 24, 6: 4, 7: 56, 10: 24, 11: 20, 12: 1124, 13: 16, 14: 44, 15: 40, 16: 4, 18: 4, 19: 12, 20: 32, 22: 16, 23: 624, 24: 48, 25: 984, 26: 24, 27: 48, 34: 20, 40: 4, 44: 24, 47: 24, 54: 20, 66: 24, 69: 8, 70: 4, 71: 68, 72: 648, 73: 60, 74: 996, 76: 44, 77: 12, 78: 8, 79: 36, 80: 72, 81: 36, 82: 980, 83: 72, 84: 20, 86: 4, 88: 24, 89: 704}

  mid-gray
  rgba8: [128, 128, 128, 255]
  groundHash: 66ac3c62ca3248fa4b4a6dd807efdc359eb8f5e05345a314a370522c19cc0dc4
  proposalHash: 7690e25361d547c644145e68e2c8c172f253b28173be1dab77710a1462fb6f51
  prospective matrix: de4e8801ace24825782edf15565914baf95a281091980d8b621b5c8451b1da32
  unique RGB colors: 100
  encoded luma range: [127, 255]
  transparency: {'zeroAlphaParentPixelsReceiveGround': 181656, 'partialAlphaParentPixelsComposited': 10344, 'opaqueParentPixels': 38400, 'hiddenNonzeroRGBAtParentAlphaZero': 0, 'partialAlphaResultRGBChangedFromSource': 10344, 'nonzeroAlphaPixelsMatchingGroundRGB': 1660}
  partial-alpha |luma-ground| histogram: {0: 1628, 1: 1580, 2: 100, 3: 60, 5: 44, 6: 1140, 7: 84, 8: 4, 9: 16, 10: 32, 11: 640, 12: 1032, 13: 72, 17: 20, 20: 4, 22: 24, 23: 24, 27: 20, 33: 24, 34: 8, 35: 72, 36: 708, 37: 996, 38: 56, 39: 44, 40: 108, 41: 1052, 42: 20, 43: 4, 44: 728}

NUMERIC OBSERVATION ONLY
  comparisonHash: 715a1fe413a0e1595b2f9c4d47fb0f6bf1b80ea4aba6616dbdc34e212e54db30
  Prospective matrices are ephemeral, never encoded, persisted as images or displayed.
  Only hashes/counts/histograms persist; no 005 projection exists.

EXACT PRESENTATION RULES
  {'operation': 'page source-over opaque solid ground; same dimensions; straight RGBA8', 'compositing': 'Pillow Image.alpha_composite(destinationRGBA, sourceRGBA); source-over; straight 8-bit RGBA input/output; pinned imaging-binary integer arithmetic/rounding', 'opaqueChannelArithmetic': 'N=Cs*As+Cg*(255-As); Q=128*N+16384; Cout=((Q>>8)+Q)>>15; Aout=255; As=0 copies ground exactly', 'quantization': 'Pillow 12.1.1 AlphaComposite.c PRECISION_BITS=7 and SHIFTFORDIV255; pinned native binary', 'outputMode': 'RGBA8; every output alpha byte 255', 'encoder': 'png-rgba-unfiltered-stored/v0: PNG signature; IHDR RGBA8; one IDAT; row filter 0; zlib 0x7801 stored blocks <=65535; Adler32; IEND; CRC32; no metadata', 'pixelMatrixIdentity': 'SHA256(canonical UTF-8 JSON {schema:static-collective/rgba-pixel-matrix/v0,width,height,mode:RGBA} + NUL + row-major RGBA8 bytes)', 'color': '8-bit RGBA; preserve encoded RGB channel values; no linear-light, profile or gamma conversion', 'transforms': {'resize': False, 'crop': False, 'blur': False, 'colorCorrection': False, 'gammaProfileConversion': False, 'motion': False}, 'measurement': 'encoded-channel luma proxy Y8=floor((2126*R+7152*G+722*B+5000)/10000); absolute Y8 difference from ground; no linearization, perceptual/physical/WCAG claim'}

IMPLEMENTATION WITNESS
  {'renderer': 'mangalize-005/solid-ground/v0', 'implementationSha256': 'f62d51f9f7e958100dd34ea729488a14566cb4be265286e2c7c7c81afa918e19', 'rasterDependency': {'renderer': 'mangalize-004/static-raster/v0', 'implementationSha256': 'ae71f5c95baa2b15a92b353275af8781449713a6fdf45166a2af983231f534e6', 'pillowVersion': '12.1.1', 'pillowImageModuleSha256': '3e5ecdcc3e8800749901e61c8108bd3c49063d3ba444fa0b62b0c18af022007f', 'pillowImagingBinarySha256': '9b24b0f90f620e6e8882e8239081fe244cd4df8f26a5df7773049e4d87779288', 'pythonAbi': 'cpython-312', 'system': 'Linux', 'machine': 'x86_64'}}

REQUESTED LATER AUTHORITY
  presentation = true for one exact externally selected proposal
  publication / printAdmission / motion / sound / externalGeneration / characterCasting / sourceMutation = false

UNCHANGED
  MANGALIZE-001/002/003/004 and the exact transparent founding raster.
  Full LemonPRESS locator and all four event lineages remain bound in every proposal.

EXPOSED BOUNDARY
  Independent ground authorship remains unproven until external selection/admission.
  Numeric contrast observations describe consequences and cannot select their context.
