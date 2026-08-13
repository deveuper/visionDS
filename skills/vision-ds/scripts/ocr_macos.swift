import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1 else {
    FileHandle.standardError.write(Data("用法: swift ocr_macos.swift <图片路径>\n".utf8))
    exit(2)
}

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write(Data("无法读取图片: \(imagePath)\n".utf8))
    exit(1)
}

let textRequest = VNRecognizeTextRequest()
textRequest.recognitionLevel = .accurate
textRequest.usesLanguageCorrection = true
if #available(macOS 13.0, *) {
    textRequest.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
}

let classifyRequest = VNClassifyImageRequest()

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([textRequest, classifyRequest])
} catch {
    FileHandle.standardError.write(Data("识别失败: \(error.localizedDescription)\n".utf8))
    exit(1)
}

for observation in textRequest.results ?? [] {
    if let candidate = observation.topCandidates(1).first {
        print("TEXT: \(candidate.string)")
    }
}

if let classifications = classifyRequest.results {
    for observation in classifications.prefix(10) where observation.confidence > 0.3 {
        print("LABEL: \(observation.identifier) (\(String(format: "%.2f", observation.confidence)))")
    }
}
