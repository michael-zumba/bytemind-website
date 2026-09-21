import Foundation
import Vision
import AppKit

// Usage: swift ocr.swift <image-path>
// Prints recognized lines as: text | x,y,w,h (pixels, top-left origin)

guard CommandLine.arguments.count > 1 else {
    print("usage: ocr <image>")
    exit(1)
}

let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let tiff = img.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff),
      let cg = rep.cgImage else {
    print("cannot load image")
    exit(1)
}

let width = cg.width
let height = cg.height
let request = VNRecognizeTextRequest { req, _ in
    guard let observations = req.results as? [VNRecognizedTextObservation] else { return }
    for obs in observations {
        guard let top = obs.topCandidates(1).first else { continue }
        let b = obs.boundingBox
        let x = b.origin.x * CGFloat(width)
        let y = (1 - b.origin.y - b.size.height) * CGFloat(height)
        let w = b.size.width * CGFloat(width)
        let h = b.size.height * CGFloat(height)
        print("\(top.string) | \(Int(x)),\(Int(y)),\(Int(w)),\(Int(h))")
    }
}
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([request])
