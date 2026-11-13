import PDFKit
import AppKit

let args = CommandLine.arguments
guard args.count >= 2, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
  print("uso: swift preview.swift arquivo.pdf [pasta-saida]")
  exit(1)
}
let saida = args.count > 2 ? args[2] : NSTemporaryDirectory()
for i in 0..<doc.pageCount {
  let img = doc.page(at: i)!.thumbnail(of: NSSize(width: 900, height: 1273), for: .mediaBox)
  let png = NSBitmapImageRep(data: img.tiffRepresentation!)!.representation(using: .png, properties: [:])!
  let caminho = (saida as NSString).appendingPathComponent("pagina-\(i + 1).png")
  try! png.write(to: URL(fileURLWithPath: caminho))
  print(caminho)
}
