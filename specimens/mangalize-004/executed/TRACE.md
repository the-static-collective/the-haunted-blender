# MANGALIZE EVENT 004

SEPARATELY ADMITTED PIXEL EXECUTION
  executionHash: c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f
  admissionHash: 1196ea5d317addd4f0c9f1c254a46de1c4312cd5550685a86e9ae7b15e48004f
  finalArtifact: {"byteLength":922098,"encodedArtifactSha256":"2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74","format":"PNG","height":360,"mode":"RGBA","path":"manga-page.png","pixelMatrixHash":"ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5","width":640}

LAYOUT
  fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a
PLAN
  b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a
PROPOSAL
  2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b

USE RECIPES
  poster | page-asset:4730b32b3e6a6a201762cb0c
  useHash: eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3
  artifact SHA: 674a270d4a1d2aa451d713b19e4889fc2886d4a6d1961f83563f9b16007f92e7
  sourceRasterDimensions: [64,96]
  scaledRasterDimensions: [128,192]
  destinationBoxBeforeClipping: [32,48,160,240]
  canvasIntersection: [32,48,160,240]
  pixelsClipped: {"bottom":0,"left":0,"right":0,"top":0}
  finalCompositedRectangle: [32,48,160,240]
  layerRaster: {"byteLength":922098,"encodedArtifactSha256":"c4f0c6665463a58a75c364e53f04512968794316f010691ec1004092a7cad593","height":360,"mode":"RGBA","path":"layers/eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3.raster.png","pixelMatrixHash":"b24a2ff65ab1215de3f2bc61904ad20d3df7295b4a2d6359cce696341ba1402a","width":640}
  cutaway | page-asset:3303923667b99a06c7417376
  useHash: ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5
  artifact SHA: 0754b290a875411d4ea81e48ee433c841bd00f5627c2a1516cc24a5f24c400a8
  sourceRasterDimensions: [40,60]
  scaledRasterDimensions: [96,144]
  destinationBoxBeforeClipping: [224,72,320,216]
  canvasIntersection: [224,72,320,216]
  pixelsClipped: {"bottom":0,"left":0,"right":0,"top":0}
  finalCompositedRectangle: [224,72,320,216]
  layerRaster: {"byteLength":922098,"encodedArtifactSha256":"889252a965388b361df876e9d866d1983e5aba61c95f052a1730ca66364b4c5b","height":360,"mode":"RGBA","path":"layers/ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5.raster.png","pixelMatrixHash":"a993cb0dd885263efc88d6b229cc7c4c72df36aa09ed4d1391263ffb308f5b7a","width":640}
  texture | page-asset:a622c44b71a723710826149f
  useHash: 7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde
  artifact SHA: f617cc565a42f9028ac77dfc444e398ad5642d956c2a9718d8cc3c2adaad2580
  sourceRasterDimensions: [64,96]
  scaledRasterDimensions: [128,192]
  destinationBoxBeforeClipping: [448,48,576,240]
  canvasIntersection: [448,48,576,240]
  pixelsClipped: {"bottom":0,"left":0,"right":0,"top":0}
  finalCompositedRectangle: [448,48,576,240]
  layerRaster: {"byteLength":922098,"encodedArtifactSha256":"3260c54a5c664f461fc4210bab7f5d699d6ccf90748af68cfa9855c3ecbab449","height":360,"mode":"RGBA","path":"layers/7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde.raster.png","pixelMatrixHash":"a18e1bbfbe0d449991f5368d1141e2a664e2e67f34417ceed1789aa2091a87aa","width":640}

EXACT RASTER SEMANTICS
  background: {"mode":"RGBA","reason":"layout has no authored background","rgba":[0,0,0,0]}
  bounds: {"maxDimension":16384,"maxRasterPixels":16777216}
  clipping: "intersection of half-open scaled destination box with [0,0,width,height]; no source crop authorship"
  color: "8-bit RGBA; preserve encoded RGB channel values; no linear-light, profile or gamma conversion"
  compositing: "Pillow Image.alpha_composite(destinationRGBA, sourceRGBA); source-over; straight 8-bit RGBA input/output; pinned imaging-binary integer arithmetic/rounding"
  coordinates: "x/y millipixels divisible by 1000 only; exact integer division; fractional origins refuse"
  encoder: "png-rgba-unfiltered-stored/v0: PNG signature; IHDR RGBA8; one IDAT; row filter 0; zlib 0x7801 stored blocks <=65535; Adler32; IEND; CRC32; no metadata"
  fit: "native-scale; no crop or time range"
  opacity: "A_out=floor((2*A_in*opacityMillionths+1000000)/2000000); RGB unchanged after resize; straight RGBA"
  ordering: ["z-ascending","useHash-lexicographic-ascending"]
  pixelMatrixIdentity: "SHA256(canonical UTF-8 JSON {schema:static-collective/rgba-pixel-matrix/v0,width,height,mode:RGBA} + NUL + row-major RGBA8 bytes)"
  placement: "copy clipped straight RGBA onto transparent full-canvas layer via paste without mask, not an additional blend"
  rotation: "zero only; nonzero refuses"
  sampling: {"conversion":"Pillow Image.convert(RGBA); no ICC/gamma transform; nonanimated PNG only","enum":1,"kernel":"LANCZOS","resize":"Pillow Image.resize(targetSize, enum, box=None, reducing_gap=None)","resizeAlpha":"unchanged dimensions: copy RGBA; otherwise straight RGBA -> premultiplied RGBa -> resize -> straight RGBA"}
  scale: "max(1, floor((2*sourceDimension*scaleMillionths+1000000)/2000000)); positive half-up"

IMPLEMENTATION
  {"implementationSha256":"ae71f5c95baa2b15a92b353275af8781449713a6fdf45166a2af983231f534e6","machine":"x86_64","pillowImageModuleSha256":"3e5ecdcc3e8800749901e61c8108bd3c49063d3ba444fa0b62b0c18af022007f","pillowImagingBinarySha256":"9b24b0f90f620e6e8882e8239081fe244cd4df8f26a5df7773049e4d87779288","pillowVersion":"12.1.1","pythonAbi":"cpython-312","renderer":"mangalize-004/static-raster/v0","system":"Linux"}

OUTPUT
  {"format":"PNG","height":360,"mode":"RGBA","width":640}

EXECUTED AUTHORITY
  {"characterCasting":false,"externalGeneration":false,"motion":false,"pixelExecution":true,"publication":false,"sound":false}

PUBLICATION / MOTION / SOUND / RECOGNITION
  Not admitted.
